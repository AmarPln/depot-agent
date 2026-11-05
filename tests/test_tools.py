"""Tests für Tools und Dispatcher, ohne LLM-Aufrufe."""
import json

import pytest

import audit
from tools import execute_tool, get_portfolio, list_funds, list_my_customers


@pytest.fixture(autouse=True)
def log_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "LOG_PATH", tmp_path / "audit.log")
    return tmp_path / "audit.log"


def test_list_funds_max_risk():
    """Der Filter max_risk lässt nur Fonds bis zur Risikoklasse durch."""
    funds = list_funds(max_risk=3)
    assert len(funds) == 4
    assert all(f["risk_class"] <= 3 for f in funds)


def test_get_portfolio_totals():
    """Gesamtwert und Gesamtgewinn von Kunde 1 stimmen."""
    portfolio = get_portfolio(1)
    assert portfolio["total_value"] == 77600
    assert portfolio["total_profit"] == 11500


def test_get_portfolio_unknown_customer():
    """Ein nicht existierender Kunde ergibt ein leeres Depot."""
    assert get_portfolio(999)["positions"] == []


def test_list_my_customers():
    """Ein Berater sieht seine Kunden, ein Kunde hat keinen Zugriff."""
    assert [c["id"] for c in list_my_customers("advisor_schmidt")] == [1, 2]
    assert list_my_customers("customer_1") == []


def test_execute_tool_denied_and_logged(log_in_tmp):
    """Ein verbotener Aufruf liefert 'Access denied' und landet im Log."""
    result = json.loads(execute_tool("customer_1", "get_portfolio", {"customer_id": 3}))
    assert result == {"error": "Access denied"}
    entry = json.loads(log_in_tmp.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["decision"] == "denied"


def test_execute_tool_bad_arguments():
    """Unerwartete Argumente vom LLM ergeben ein Fehler-JSON statt eines Absturzes."""
    result = json.loads(execute_tool("customer_1", "list_funds", {"unknown": 1}))
    assert "error" in result
