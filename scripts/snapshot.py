"""Freeze SMIL animations into a static final frame.

GitHub runs SMIL, but `rsvg-convert`, og:image scrapers and most image
previewers do not: they show frame 0, where every animated group is still
`opacity="0"`. A snapshot removes the animation elements and pins the final
state, which is what you want for docs, screenshots and layout checks.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ANIMATION_TAGS = {"animate", "animateTransform", "animateMotion",
                  "animateColor", "set"}


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _final_value(element):
    """Value an animation leaves behind: `to`/last `values` when it freezes,
    otherwise the first frame (blink cursors start visible)."""
    if element.get("fill") == "freeze":
        if element.get("to") is not None:
            return element.get("to")
        values = element.get("values")
        if values:
            return values.split(";")[-1]
        return element.get("from")
    values = element.get("values")
    if values:
        return values.split(";")[0]
    return element.get("from") or element.get("to")


def freeze(svg_text):
    root = ET.fromstring(svg_text)

    # Bake each animation's end state into its parent before dropping it:
    # without this, bars stay at width="0" and typed text stays clipped.
    for parent in list(root.iter()):
        for child in list(parent):
            if _local(child.tag) not in ANIMATION_TAGS:
                continue
            attribute = child.get("attributeName")
            value = _final_value(child)
            if attribute and value is not None:
                parent.set(attribute, value)
            parent.remove(child)

    for parent in list(root.iter()):
        for child in list(parent):
            if _local(child.tag) == "clipPath":
                parent.remove(child)

    for element in root.iter():
        element.attrib.pop("clip-path", None)
        if element.get("opacity") == "0":
            element.set("opacity", "1")
        if element.get("transform") == "translate(0 8)":
            element.set("transform", "translate(0 0)")

    return ET.tostring(root, encoding="unicode") + "\n"


def write_snapshot(source, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(freeze(Path(source).read_text(encoding="utf-8")),
                      encoding="utf-8")
    return target


def write_all(dist_dir, out_dir):
    written = []
    for source in sorted(Path(dist_dir).glob("*.svg")):
        written.append(write_snapshot(source, Path(out_dir) / source.name))
    return written
