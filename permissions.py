"""Berechtigungen: feste Nutzer und die Prüfung jedes Tool-Aufrufs."""

USERS = {
    "customer_1": {"role": "customer", "customer_id": 1},
    "advisor_schmidt": {"role": "advisor", "customers": [1, 2]},
    "admin": {"role": "admin"},
}

KNOWN_TOOLS = {"list_funds", "get_portfolio", "list_my_customers"}


def _read_customer_id(args: dict) -> int | None:
    """Liest customer_id aus den LLM-Argumenten, ungültige Werte ergeben None."""
    value = args.get("customer_id")
    if value is None or isinstance(value, bool):  # True == 1 in Python, daher extra abfangen
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def is_allowed(user: str, tool: str, args: dict) -> bool:
    """Entscheidet, ob user das Tool mit diesen Argumenten aufrufen darf.
    Alles, was nicht ausdrücklich erlaubt ist, wird verweigert.
    """
    account = USERS.get(user)
    if account is None or tool not in KNOWN_TOOLS:
        return False
    role = account["role"]

    if role == "admin":
        return True
    if tool == "list_funds":
        return True
    if tool == "get_portfolio":
        customer_id = _read_customer_id(args)
        if customer_id is None:
            return False
        if role == "customer":
            return customer_id == account["customer_id"]
        if role == "advisor":
            return customer_id in account["customers"]
    if tool == "list_my_customers":
        return role == "advisor"
    return False
