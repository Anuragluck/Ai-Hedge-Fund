import json
from datetime import datetime, timezone

AUDIT_FILE = "audit_log.jsonl"


def append_audit_record(record, path=AUDIT_FILE):
    record = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        **record,
    }

    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, separators=(",", ":")) + "\n")
        file.flush()