"""Die drei Tools des Agenten, ihre Schemas für das LLM und der Dispatcher."""
import json
import time
from contextlib import closing

import audit
from db import get_connection
from permissions import USERS, is_allowed

# Kategorien exakt so, wie sie in der Datenbank stehen.
CATEGORIES = ["Aktien", "Renten", "Mischfonds", "Immobilien", "Geldmarkt"]


def list_funds(category: str | None = None, max_risk: int | None = None) -> list[dict]:
    """Listet Fonds, optional gefiltert nach Kategorie und maximaler Risikoklasse."""
    sql = "SELECT id, name, kategorie AS category, risikoklasse AS risk_class, kurs AS price FROM fonds WHERE 1=1"
    params: list = []
    if category is not None:
        sql += " AND kategorie = ?"
        params.append(category)
    if max_risk is not None:
        sql += " AND risikoklasse <= ?"
        params.append(max_risk)
    sql += " ORDER BY name"
    with closing(get_connection()) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_portfolio(customer_id: int) -> dict:
    """Liefert die Positionen eines Kunden mit Wert und Gewinn sowie die Summen.
    Ein unbekannter Kunde ergibt ein leeres Depot.
    """
    sql = """
        SELECT f.name, f.kategorie, p.anteile, p.einstandskurs, f.kurs
        FROM positionen p JOIN fonds f ON f.id = p.fonds_id
        WHERE p.kunde_id = ? ORDER BY f.name
    """
    with closing(get_connection()) as conn:
        rows = conn.execute(sql, (customer_id,)).fetchall()

    positions = []
    for r in rows:
        value = r["anteile"] * r["kurs"]
        positions.append({
            "fund": r["name"],
            "category": r["kategorie"],
            "shares": r["anteile"],
            "value": round(value, 2),
            "profit": round(value - r["anteile"] * r["einstandskurs"], 2),
        })
    return {
        "customer_id": customer_id,
        "positions": positions,
        "total_value": round(sum(p["value"] for p in positions), 2),
        "total_profit": round(sum(p["profit"] for p in positions), 2),
    }


def list_my_customers(user: str) -> list[dict]:
    """Listet die Kunden des Beraters. user kommt aus dem Code, nie vom LLM."""
    customer_ids = USERS.get(user, {}).get("customers", [])
    if not customer_ids:
        return []
    placeholders = ",".join("?" * len(customer_ids))
    sql = f"SELECT id, name, typ AS type FROM kunden WHERE id IN ({placeholders}) ORDER BY id"
    with closing(get_connection()) as conn:
        return [dict(r) for r in conn.execute(sql, customer_ids).fetchall()]


TOOL_SCHEMAS = [
    {
        "name": "list_funds",
        "description": (
            "Listet verfügbare Fonds mit Kategorie, Risikoklasse (1 = sehr sicher, "
            "7 = sehr riskant) und aktuellem Kurs. Optional filterbar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": CATEGORIES},
                "max_risk": {"type": "integer", "minimum": 1, "maximum": 7},
            },
        },
    },
    {
        "name": "get_portfolio",
        "description": (
            "Liefert das Depot eines Kunden: Positionen mit Wert und Gewinn "
            "sowie Gesamtwert und Gesamtgewinn in Euro."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "integer", "description": "ID des Kunden"}},
            "required": ["customer_id"],
        },
    },
    {
        "name": "list_my_customers",
        "description": "Listet die Kunden des angemeldeten Beraters (ID, Name, Typ).",
        "input_schema": {"type": "object", "properties": {}},
    },
]

TOOLS = {
    "list_funds": list_funds,
    "get_portfolio": get_portfolio,
    "list_my_customers": list_my_customers,
}


def execute_tool(user: str, name: str, args: dict) -> str:
    """Prüft die Berechtigung, führt das Tool aus und protokolliert den Aufruf.
    Gibt das Ergebnis oder einen Fehler als JSON-String für das LLM zurück.
    """
    start = time.perf_counter()

    def finish(result, decision: str) -> str:
        audit.log_tool_call(user, name, args, decision, (time.perf_counter() - start) * 1000)
        return json.dumps(result, ensure_ascii=False, default=str)

    if not is_allowed(user, name, args):
        return finish({"error": "Access denied"}, "denied")
    try:
        if name == "list_my_customers":
            result = list_my_customers(user)
        else:
            result = TOOLS[name](**args)
    except Exception as e:
        return finish({"error": f"Tool error: {e}"}, "error")
    return finish(result, "allowed")
