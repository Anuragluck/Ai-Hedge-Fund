import json
from datetime import datetime, timezone

AUDIT_FILE = "audit_log.jsonl"


def append_audit_record(record, path=AUDIT_FILE):
    """One JSON object per line, appended. Nothing is ever rewritten."""
    record = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str, separators=(",", ":")) + "\n")