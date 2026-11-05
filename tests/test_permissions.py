"""Tests für is_allowed: eine Tabelle aus Nutzer, Tool, Argumenten und Erwartung."""
import pytest

from permissions import is_allowed


@pytest.mark.parametrize("user,tool,args,expected", [
    ("customer_1", "get_portfolio", {"customer_id": 1}, True),
    ("customer_1", "get_portfolio", {"customer_id": 3}, False),
    ("customer_1", "list_my_customers", {}, False),
    ("customer_1", "list_funds", {}, True),
    ("advisor_schmidt", "get_portfolio", {"customer_id": 1}, True),
    ("advisor_schmidt", "get_portfolio", {"customer_id": 2}, True),
    ("advisor_schmidt", "get_portfolio", {"customer_id": 3}, False),
    ("advisor_schmidt", "list_my_customers", {}, True),
    ("admin", "get_portfolio", {"customer_id": 3}, True),
    ("hacker", "list_funds", {}, False),
    ("customer_1", "drop_table", {}, False),
    ("admin", "drop_table", {}, False),
    ("customer_1", "get_portfolio", {}, False),
    ("customer_1", "get_portfolio", {"customer_id": "1"}, True),
    ("customer_1", "get_portfolio", {"customer_id": "three"}, False),
    ("customer_1", "get_portfolio", {"customer_id": True}, False),
])
def test_is_allowed(user, tool, args, expected):
    assert is_allowed(user, tool, args) is expected
