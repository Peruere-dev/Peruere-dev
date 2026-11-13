"""Render README.md from profile.json, so the profile text and the images
never drift apart. Images are pulled from the `output` branch over raw URLs
(local relative paths are also fine for the card, which is committed).
"""
from urllib.parse import quote


def _badge(badge, handle):
    label = quote(str(badge["label"]).replace("-", "--"), safe="")
    value = quote(str(badge["value"]).replace("-", "--"), safe="")
    url = (f"https://img.shields.io/badge/{label}-{value}-{badge['color']}"
           f"?style=flat-square&logo={badge.get('logo', 'github')}")
    if badge.get("logoColor"):
        url += f"&logoColor={badge['logoColor']}"
    alt = f"{badge['label']}: {badge['value']}"
    return f'<a href="{badge["href"]}"><img src="{url}" alt="{alt}"></a>'


def render(cfg):
    user = cfg["user"]
    handle = user["handle"]
    raw = f"https://raw.githubusercontent.com/{handle}/{handle}/output"
    badges = "\n".join(_badge(badge, handle) for badge in user["badges"])
    stack = ",".join(user["stack"])
    alt = " ".join(part for part in (
        user["name"], "—", user["tagline"],
        str(user.get("tagline_cn", "")).strip()) if part)

    return f'''<!-- generated from profile.json by scripts/build.py — edit the config, not this file -->
<div align="center">

<img src="{raw}/character-card.svg" alt="{alt}" width="100%">

{badges}

<img src="{raw}/app-console.svg" alt="Live repository console: stars, forks, open issues and last push" width="100%">

<img src="https://skillicons.dev/icons?i={stack}" alt="{stack.replace(",", ", ")}">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{raw}/github-snake-dark.svg">
  <img src="{raw}/github-snake.svg" alt="A snake eating my contribution graph">
</picture>

</div>
'''


def generate(cfg, path):
    path.write_text(render(cfg), encoding="utf-8")
    return path
