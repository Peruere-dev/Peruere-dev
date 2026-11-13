#!/usr/bin/env python3
"""Layout smoke test.

Rasterizes the frozen snapshots and asserts that each named region actually
contains ink -- this catches "everything is invisible", elements pushed off
the canvas and collided rows, which XML validation cannot see.

Regions are expressed as fractions of the panel size, so changing the number
of skill bars or log lines does not invalidate them.

Dev-only: needs `rsvg-convert` and Pillow. `python3 scripts/check.py`
"""
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required for the layout check: pip install pillow")

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "dist" / "snapshot"
ZOOM = 2
INK_THRESHOLD = 90  # dark themes: anything brighter than this is content

# file -> [(region, fx0, fy0, fx1, fy1), ...] in 0..1 of the panel size
REGIONS = {
    "character-card.svg": [
        ("title", 0.40, 0.14, 0.85, 0.25),
        ("name", 0.40, 0.25, 0.69, 0.38),
        ("bars", 0.58, 0.48, 0.90, 0.92),
        ("emblem", 0.02, 0.05, 0.36, 0.95),
        ("footer", 0.68, 0.90, 0.98, 1.00),
    ],
    "terminal.svg": [
        ("titlebar", 0.36, 0.01, 0.64, 0.09),
        ("first-line", 0.02, 0.12, 0.50, 0.20),
        ("body", 0.02, 0.38, 0.86, 0.84),
        ("cursor", 0.02, 0.88, 0.17, 1.00),
    ],
    "app-console.svg": [
        ("titlebar", 0.35, 0.01, 0.66, 0.09),
        ("log", 0.02, 0.10, 0.95, 0.56),
        ("prompt", 0.02, 0.50, 0.28, 0.60),
        ("tiles", 0.02, 0.60, 0.98, 0.85),
        ("footer", 0.02, 0.86, 0.98, 1.00),
    ],
}


def ink_ratio(image, box):
    histogram = image.crop(box).convert("L").histogram()
    lit = sum(histogram[INK_THRESHOLD + 1:])
    return lit / max(sum(histogram), 1)


def main():
    if not SNAPSHOTS.is_dir():
        sys.exit("no snapshots: run python3 scripts/build.py first")
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for snapshot in sorted(SNAPSHOTS.glob("*.svg")):
            regions = REGIONS.get(snapshot.name)
            if not regions:
                continue
            png = Path(tmp) / (snapshot.stem + ".png")
            subprocess.run(["rsvg-convert", "-w", str(1000 * ZOOM // 1),
                            str(snapshot), "-o", str(png)], check=True)
            image = Image.open(png)
            print(f"\n{snapshot.name}  {image.width}x{image.height}")
            for label, fx0, fy0, fx1, fy1 in regions:
                box = (int(fx0 * image.width), int(fy0 * image.height),
                       int(fx1 * image.width), int(fy1 * image.height))
                ratio = ink_ratio(image, box)
                status = "ok" if ratio >= 0.002 else "EMPTY"
                print(f"  {label:<12} ink={ratio:6.2%}  {status}")
                if ratio < 0.002:
                    failures.append(f"{snapshot.name}:{label} is blank")

    if failures:
        print("\nFAILED:")
        for failure in failures:
            print("  -", failure)
        return 1
    print("\nall regions have content")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
