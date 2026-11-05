"""Audit-Log: schreibt jeden Tool-Aufruf als JSON-Zeile in audit.log."""
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "audit.log"


def log_tool_call(user: str, tool: str, args: dict, decision: str, duration_ms: float) -> None:
    """Hängt einen Eintrag an (decision: allowed, denied oder error)."""
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "tool": tool,
        "args": args,
        "decision": decision,
        "duration_ms": round(duration_ms, 2),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
