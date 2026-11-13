#!/usr/bin/env python3
"""Layout smoke test.

Rasterizes the frozen snapshots and asserts that each named region actually
contains ink -- this catches "everything is invisible", elements pushed off
the canvas and collided rows, which XML validation cannot see.

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

# name -> (viewBox width, [(region, x0, y0, x1, y1), ...])
REGIONS = {
    "character-card.svg": (820, [
        ("title", 330, 52, 700, 80),
        ("name", 330, 84, 560, 120),
        ("bars", 480, 160, 745, 270),
        ("emblem", 40, 30, 280, 270),
        ("footer", 560, 270, 800, 296),
    ]),
    "terminal.svg": (820, [
        ("titlebar", 300, 6, 520, 32),
        ("first-line", 20, 44, 400, 74),
        ("body", 20, 140, 700, 300),
        ("cursor", 20, 320, 130, 360),
    ]),
    "app-console.svg": (850, [
        ("titlebar", 300, 6, 560, 32),
        ("log", 20, 44, 800, 232),
        ("prompt", 20, 220, 220, 250),
        ("tiles", 24, 258, 828, 356),
        ("footer", 20, 366, 830, 418),
    ]),
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
            spec = REGIONS.get(snapshot.name)
            if not spec:
                continue
            width, regions = spec
            png = Path(tmp) / (snapshot.stem + ".png")
            subprocess.run(["rsvg-convert", "-w", str(width * ZOOM),
                            str(snapshot), "-o", str(png)], check=True)
            image = Image.open(png)
            scale = image.width / width
            print(f"\n{snapshot.name}  {image.width}x{image.height}")
            for label, x0, y0, x1, y1 in regions:
                box = (int(x0 * scale), int(y0 * scale),
                       int(x1 * scale), int(y1 * scale))
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
