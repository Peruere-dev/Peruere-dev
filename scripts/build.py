#!/usr/bin/env python3
"""Build every profile asset from profile.json.

    python3 scripts/build.py                 # fetch live stats
    python3 scripts/build.py --offline       # sample numbers, no network
    python3 scripts/build.py --only card     # rebuild a single asset
    python3 scripts/build.py --out dist      # where the SVGs land
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import gen_card      # noqa: E402
import gen_console   # noqa: E402
import gen_readme    # noqa: E402
import snapshot      # noqa: E402
import gen_terminal  # noqa: E402

TARGETS = {
    "card": (gen_card, "character-card.svg"),
    "terminal": (gen_terminal, "terminal.svg"),
    "console": (gen_console, "app-console.svg"),
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(ROOT / "profile.json"),
                        help="path to the JSON config")
    parser.add_argument("--out", default=str(ROOT / "dist"))
    parser.add_argument("--offline", action="store_true",
                        help="use sample stats instead of calling the API")
    parser.add_argument("--only", action="append", choices=sorted(TARGETS),
                        help="build only these targets (repeatable)")
    parser.add_argument("--no-readme", action="store_true")
    parser.add_argument("--no-snapshot", action="store_true",
                        help="skip the frozen static frames in dist/snapshot")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for name in args.only or TARGETS:
        module, filename = TARGETS[name]
        if name == "console":
            module.generate(cfg, out / filename, offline=args.offline)
        else:
            module.generate(cfg, out / filename)
        print(f"wrote {out / filename}")

    if not args.no_snapshot:
        for written_path in snapshot.write_all(out, out / "snapshot"):
            print(f"wrote {written_path}")

    if cfg.get("emit_readme") and not args.no_readme:
        gen_readme.generate(cfg, ROOT / "README.md")
        print(f"wrote {ROOT / 'README.md'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
