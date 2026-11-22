"""Layer 1 - structural validation against the spec's Output Schema Contract."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schema" / "output.schema.json").read_text())
_VALIDATOR = Draft202012Validator(SCHEMA)


def check(output) -> list:
    if not isinstance(output, dict):
        return [{"rule": "OSC-1", "message": "output is not a JSON object"}]
    return [
        {"rule": "OSC-1", "message": e.message, "path": "/".join(map(str, e.absolute_path))}
        for e in sorted(_VALIDATOR.iter_errors(output), key=lambda e: list(e.absolute_path))
    ]
