"""Game-style character card.

Height adapts to the number of skill bars, so the config can hold four, five
or six of them without colliding with the footer. All motion is SMIL:
twinkling stars, a counter-rotating emblem and bars that ease out from zero.
Regenerate with: python3 scripts/build.py
"""
import random

import svg_kit as kit

CW = 820
STAR_SEED = 618  # fixed seed => stable artwork across runs
STAR_COUNT = 46
BARS_X, BARS_Y, BAR_STEP = 330, 176, 28
TRACK_X, TRACK_W, TRACK_H = BARS_X + 150, 250, 8
BOTTOM_PAD = 40


def height_for(bar_count):
    return BARS_Y + (bar_count - 1) * BAR_STEP + BOTTOM_PAD


def _stars(width, height, count=STAR_COUNT, seed=STAR_SEED):
    rnd = random.Random(seed)
    lines = []
    for _ in range(count):
        cx, cy = rnd.randint(0, width), rnd.randint(0, height)
        radius = rnd.choice([0.8, 1, 1.3])
        dur, begin = rnd.uniform(2, 5), rnd.uniform(0, 3)
        lines.append(
            f'    <circle cx="{cx}" cy="{cy}" r="{radius}" fill="#fff">'
            f'<animate attributeName="opacity" values="0.15;0.9;0.15" '
            f'dur="{dur:.1f}s" begin="{begin:.1f}s" repeatCount="indefinite"/>'
            f'</circle>')
    return "\n".join(lines)


def _emblem(initial, center):
    return f'''  <g transform="translate(160 {center})">
    <circle r="92" fill="none" stroke="url(#gold)" stroke-width="1.5" stroke-dasharray="4 8">
      <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="40s" repeatCount="indefinite"/>
    </circle>
    <g>
      <polygon points="0,-78 67,-39 67,39 0,78 -67,39 -67,-39" fill="#ffffff08" stroke="url(#gold)" stroke-width="2"/>
      <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="60s" repeatCount="indefinite"/>
    </g>
    <circle r="58" fill="#141a33" stroke="url(#gold)" stroke-width="2"/>
    <text y="22" text-anchor="middle" font-size="64" font-weight="700" fill="url(#gold)" font-family="Georgia,'Times New Roman',serif">{kit.esc(initial)}</text>
    <g fill="url(#gold)">
      <path d="M0,-104 l4,8 -4,8 -4,-8z"/><path d="M0,104 l4,-8 -4,-8 -4,8z"/>
    </g>
  </g>'''


def _bars(stats):
    lines = []
    for index, stat in enumerate(stats):
        y = BARS_Y + index * BAR_STEP
        value = stat["value"]
        shown = kit.esc(stat.get("shown", value))
        color = stat["color"]
        lines.append(
            f'    <text x="{BARS_X}" y="{y}" fill="#c9d1f0" font-size="13">{kit.esc(stat["label"])}</text>\n'
            f'    <text x="{BARS_X + 450}" y="{y}" fill="{color}" font-size="13" '
            f'text-anchor="end" font-weight="bold">{shown}</text>\n'
            f'    <rect x="{TRACK_X}" y="{y - 10}" width="{TRACK_W}" height="{TRACK_H}" '
            f'rx="4" fill="#ffffff14"/>\n'
            f'    {kit.smooth_width(TRACK_X, y - 10, TRACK_W, value / 100, color, 0.6 + index * 0.2, height=TRACK_H)}')
    return "\n".join(lines)


def render(cfg):
    user, theme, card = cfg["user"], cfg["theme"], cfg["card"]
    stats = card["stats"]
    ch = height_for(len(stats))
    center = ch // 2
    bg = theme["card_bg"]
    accent, accent_dark = theme["accent"], theme["accent_dark"]
    name = user["name"]
    rating = "★" * int(user.get("star_rating", 5))
    # rough width estimate for the 40px bold name, keeps the stars right after it
    stars_x = BARS_X + int(len(name) * 23) + 16
    tagline_cn = str(user.get("tagline_cn", "")).strip()
    quote = f'“{kit.esc(user["tagline"])}”'
    if tagline_cn:
        quote += f' — {kit.esc(tagline_cn)}'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{ch}" viewBox="0 0 {CW} {ch}" font-family="{kit.SANS}">
  <defs>
    {kit.linear_gradient("sky", [(0, bg[0]), (0.6, bg[1]), (1, bg[2])], 0, 0, 1, 1)}
    {kit.linear_gradient("gold", [(0, accent), (1, accent_dark)], 0, 0, 1, 1)}
    <radialGradient id="glow"><stop offset="0" stop-color="{accent}" stop-opacity="0.45"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
    <clipPath id="frame"><rect width="{CW}" height="{ch}" rx="16"/></clipPath>
  </defs>
  <g clip-path="url(#frame)">
    <rect width="{CW}" height="{ch}" fill="url(#sky)"/>
{_stars(CW, ch)}
    <circle cx="160" cy="{center}" r="140" fill="url(#glow)"/>
  </g>
  <rect x="1" y="1" width="{CW - 2}" height="{ch - 2}" rx="16" fill="none" stroke="url(#gold)" stroke-opacity="0.55"/>

{_emblem(user.get("initial") or name[:1].upper(), center)}

  <text x="{BARS_X}" y="70" fill="{theme["muted"]}" font-size="13" letter-spacing="3">{kit.esc(card["title"])}</text>
  <text x="{BARS_X}" y="112" fill="#fff" font-size="40" font-weight="700" letter-spacing="1">{kit.esc(name)}</text>
  <text x="{stars_x}" y="112" fill="url(#gold)" font-size="22">{rating}</text>
  <text x="{BARS_X}" y="140" fill="{theme["text"]}" font-size="15" font-style="italic">{quote}</text>
{_bars(stats)}
  <text x="{CW - 24}" y="{ch - 16}" fill="#5d6591" font-size="11" text-anchor="end">{kit.esc(card["footer"])}</text>
</svg>
'''


def generate(cfg, path):
    path.write_text(render(cfg), encoding="utf-8")
    return path
