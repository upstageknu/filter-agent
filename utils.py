import json
import re

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def safe_json_loads(raw: str) -> dict:
    text = raw.strip()
    match = _JSON_FENCE_RE.search(text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)
