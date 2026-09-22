"""Export deterministic shared schemas; --check never modifies files."""

import argparse
import json
from pathlib import Path

from pawtwin.contracts import build_domain_schema, build_openapi_schema


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parents[1] / "contracts"
    schemas = {
        "openapi.json": build_openapi_schema(),
        "domain.schema.json": build_domain_schema(),
    }
    stale = []
    for name, schema in schemas.items():
        path = directory / name
        expected = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                stale.append(name)
        else:
            directory.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
    if stale:
        print("Missing or stale contracts: " + ", ".join(stale))
        return 1
    print("Contracts are current." if args.check else "Contracts exported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
