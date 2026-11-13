"""Server-console panel with live repository stats (850 wide, height grows
with the number of log lines).

Data comes from the public GitHub API, standard library only:
    GET /repos/{repo}                      -> stars, forks, pushed_at
    GET /search/issues?q=repo:{repo}+...    -> open issue count
If the API is unreachable (rate limit, offline) the panel still renders, with
"—" in the tiles, and the build stays green.
"""
import datetime
import json
import os
import sys
import urllib.request

import svg_kit as kit

API = os.environ.get("PROFILE_API", "https://api.github.com")
W = 850
TOP, LINE_H = 62, 25
MARGIN, GAP, TILE_H = 24, 16, 92
LEVELS = {"INFO": "#7ee787", "WARN": "#f0b35b", "ERR": "#ff7b72"}


def _get(path, token=None):
    request = urllib.request.Request(
        API + path,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "profile-readme-kit"})
    if token:
        request.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def fetch(repo, token=None):
    """Return {stars, forks, issues, pushed} or None when the API fails."""
    try:
        data = _get(f"/repos/{repo}", token)
        issues = _get(f"/search/issues?q=repo:{repo}+type:issue+state:open"
                      f"&per_page=1", token)
        return {
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "issues": issues["total_count"],
            "pushed": datetime.datetime.fromisoformat(
                data["pushed_at"].replace("Z", "+00:00")),
        }
    except Exception as error:  # noqa: BLE001 - a stale panel beats a red build
        print(f"warning: could not fetch stats for {repo} ({error})",
              file=sys.stderr)
        return None


UNITS = (("y", 365 * 86400), ("mo", 30 * 86400), ("w", 7 * 86400),
         ("d", 86400), ("h", 3600), ("m", 60))


def relative(moment, now):
    """Coarse "time ago": 2y / 5mo / 3w / 4d / 7h / 12m / just now."""
    seconds = (now - moment).total_seconds()
    if seconds < 90:
        return "just now"
    for suffix, size in UNITS:
        if seconds >= size:
            return f"{int(seconds // size)}{suffix} ago"
    return "just now"


def _layout(log):
    prompt_y = TOP + len(log) * LINE_H
    tiles_top = prompt_y + 24
    bottom = tiles_top + TILE_H
    tile_w = (W - 2 * MARGIN - 3 * GAP) / 4
    return {
        "prompt_y": prompt_y,
        "tiles_top": tiles_top,
        "tile_w": tile_w,
        "bottom": bottom,
        "height": bottom + 70,
    }


def _tiles(stats, layout, begin):
    values = [
        ("STARS", "★", stats.get("stars"), "#f0b35b"),
        ("FORKS", "⑂", stats.get("forks"), "#6cc5ff"),
        ("OPEN ISSUES", "●", stats.get("issues"), "#ff7b72"),
        ("LAST PUSH", "↻", stats.get("pushed"), "#7ee787"),
    ]
    parts = []
    for index, (label, icon, value, color) in enumerate(values):
        if value is None:
            shown = "—"
        elif isinstance(value, str):
            shown = value
        else:
            shown = str(value)
        size = 34 if len(shown) <= 4 else 26
        x = MARGIN + index * (layout["tile_w"] + GAP)
        top = layout["tiles_top"]
        start = begin + index * 0.12
        parts.append(
            f'  <g opacity="0" transform="translate(0 8)">\n'
            f'    {kit.freeze_opacity(start)}\n'
            f'    <animateTransform attributeName="transform" type="translate" '
            f'from="0 8" to="0 0" begin="{start:.2f}s" dur=".35s" fill="freeze"/>\n'
            f'    <rect x="{x:.1f}" y="{top}" width="{layout["tile_w"]:.1f}" '
            f'height="{TILE_H}" rx="8" fill="#ffffff07" stroke="{color}" '
            f'stroke-opacity=".35"/>\n'
            f'    <text x="{x + 14:.1f}" y="{top + 24}" fill="#7d86a8" font-size="11" '
            f'letter-spacing="1.5">{icon} {label}</text>\n'
            f'    <text x="{x + 14:.1f}" y="{top + 66}" fill="{color}" '
            f'font-size="{size}" font-weight="bold">{kit.esc(shown)}</text>\n'
            f'  </g>')
    return "\n".join(parts)


def render(cfg, stats, now):
    console = cfg["console"]
    user = cfg["user"]
    log = [tuple(line) for line in console["log"]]
    layout = _layout(log)
    height = layout["height"]

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{height}" viewBox="0 0 {W} {height}" font-family="{kit.MONO}" font-size="13.5">
  <defs>
    {kit.linear_gradient("bg", [(0, "#0b0f17"), (1, "#111827")], 0, 0, 0, 1)}
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#ffffff05"/></pattern>
  </defs>
  {kit.window_frame(W, height, console["title"])}
  <rect width="{W}" height="{height}" rx="12" fill="url(#scan)"/>
  <circle cx="{W - 30}" cy="19" r="4" fill="#28c840"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
  <text x="{W - 42}" y="23.5" text-anchor="end" fill="#28c840" font-size="11.5">ONLINE</text>''']

    for index, (level, message) in enumerate(log):
        color = LEVELS.get(level, LEVELS["INFO"])
        stamp = (now + datetime.timedelta(seconds=index)).strftime("%H:%M:%S")
        begin = 0.4 + index * 0.55
        parts.append(
            f'  <g opacity="0">{kit.freeze_opacity(begin)}\n'
            f'    <text x="24" y="{TOP + index * LINE_H}">'
            f'<tspan fill="#56607a">[{stamp} </tspan>'
            f'<tspan fill="{color}">{level}</tspan>'
            f'<tspan fill="#56607a">]</tspan>'
            f'<tspan fill="#c9d1e6">  {kit.esc(message)}</tspan></text>\n'
            f'  </g>')

    prompt_y = layout["prompt_y"]
    begin = 0.4 + len(log) * 0.55 + 0.3
    markup, dur = kit.typed_command(
        0, MARGIN, prompt_y, "/stats", begin, prompt="> ", char_w=8.15,
        line_h=LINE_H, seconds_per_char=0.09, prompt_fill="#6cc5ff")
    parts.append(markup)
    parts.append(
        f'  <g opacity="0">{kit.freeze_opacity(begin + dur)}\n'
        f'    {kit.blink_cursor(MARGIN + (2 + len("/stats")) * 8.15 + 3, prompt_y - 12, height=15)}\n'
        f'  </g>')

    parts.append(_tiles(stats, layout, begin + 0.9))

    footer_y = layout["bottom"]
    parts.append(
        f'  <g opacity="0">{kit.freeze_opacity(begin + 1.6)}\n'
        f'    <line x1="{MARGIN}" y1="{footer_y + 26}" x2="{W - MARGIN}" y2="{footer_y + 26}" stroke="#263042"/>\n'
        f'    <text x="{MARGIN}" y="{footer_y + 54}" fill="#7d86a8" font-size="12">'
        f'{kit.esc(user["name"])} · {kit.esc(user["location"])} · Java ☕   '
        f'discord: <tspan fill="#a5b4fc">{kit.esc(user["discord"])}</tspan></text>\n'
        f'    <text x="{W - MARGIN}" y="{footer_y + 54}" text-anchor="end" '
        f'fill="#56607a" font-size="11.5">updated {now:%Y-%m-%d %H:%M} UTC · '
        f'{kit.esc(console["footer_note"])}</text>\n'
        f'  </g>\n</svg>')
    return "\n".join(parts) + "\n"


def generate(cfg, path, *, offline=False):
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    if offline:
        stats = {"stars": 40, "forks": 15, "issues": 7,
                 "pushed": now - datetime.timedelta(hours=3)}
        stats["pushed"] = relative(stats["pushed"], now)
    else:
        stats = fetch(cfg["tracked_repo"], os.environ.get("GITHUB_TOKEN")) or {}
        if stats.get("pushed"):
            stats["pushed"] = relative(stats["pushed"], now)
    path.write_text(render(cfg, stats, now), encoding="utf-8")
    return path
