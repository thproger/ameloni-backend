#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema to openapi.json and openapi.yaml.

Usage (from project root):
    python scripts/export_openapi.py

The script imports the FastAPI app instance without starting the server,
calls `app.openapi()`, and writes both JSON and YAML to the project root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    # Import after sys.path tweak so `app` package resolves from project root
    from app.main import app

    schema = app.openapi()

    json_path = ROOT / "openapi.json"
    yaml_path = ROOT / "openapi.yaml"

    json_path.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    yaml_path.write_text(
        yaml.safe_dump(schema, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    print(f"Wrote {json_path}")
    print(f"Wrote {yaml_path}")
    print(f"OpenAPI version: {schema.get('openapi')}")
    print(f"Title: {schema.get('info', {}).get('title')}")
    print(f"Paths: {len(schema.get('paths', {}))}")


if __name__ == "__main__":
    main()
