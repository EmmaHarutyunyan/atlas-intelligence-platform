import hashlib
import json


def stable_record_hash(record: dict) -> str:
    payload = {
        "url": record.get("url", ""),
        "title": record.get("title", ""),
        "content": record.get("content", ""),
        "attributes": record.get("attributes", {}),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
