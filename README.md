# Depot-Assistent mit Berechtigungsprüfung

Ein KI-Agent beantwortet Fragen zu Fonds und Depots in natürlicher Sprache.
Das LLM (Claude Haiku) wählt die Tools, **der Code prüft vor jedem Aufruf**, ob der Nutzer die Daten sehen darf.
Jede Entscheidung landet in `audit.log`.

## Start

```bash
python -m venv .venv && .venv\Scripts\activate   # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                            # Key eintragen (Linux/Mac: cp)
python main.py
```

Tests (ohne LLM, ohne API-Key): `pytest -v`


## Nutzer und Rechte

| Nutzer | Darf |
|---|---|
| `customer_1` | Fonds, eigenes Depot (Kunde 1) |
| `advisor_schmidt` | Fonds, Depots der Kunden 1 und 2, eigene Kundenliste |
| `admin` | alles |

## Sicherheitsentscheidungen

- **Prüfung im Code, nicht im Prompt:** Das LLM kann man überreden, `is_allowed` nicht. „I am admin“ in der Frage ändert nichts.
- **Default-Deny:** Was nicht ausdrücklich erlaubt ist, wird verweigert.
- **Feste Tools statt freiem SQL:** Das LLM kann nur drei definierte Abfragen auslösen, Werte laufen über `?`-Platzhalter.
- **Nutzer kommt aus dem Code:** `list_my_customers` hat keine Parameter, das LLM kann keinen anderen Nutzer angeben.
- **Read-only-DB, max. 5 Schritte, Audit-Log.**
