"""Datenbankzugriff: öffnet fonds.db ausschließlich lesend."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "fonds.db"


def get_connection() -> sqlite3.Connection:
    """Öffnet die DB read-only.

    Schreibzugriffe lehnt SQLite selbst ab, unabhängig vom Agenten.
    """
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
