"""Tiny SVG helpers shared by the generators.

Everything here targets GitHub's README renderer: <script> is stripped from
images, so motion has to come from SMIL (<animate> / <animateTransform> /
<set>) baked into the SVG itself. Standard library only.
"""
from html import escape

MONO = ("'JetBrains Mono','Cascadia Code','SFMono-Regular',Consolas,"
        "'Liberation Mono',monospace")
SANS = ("'Segoe UI','PingFang SC','Microsoft YaHei','Noto Sans CJK SC',"
        "Helvetica,Arial,sans-serif")

# macOS-style traffic lights, reused by every window-ish panel.
LIGHTS = ('<circle cx="22" cy="19" r="6" fill="#ff5f57"/>'
          '<circle cx="42" cy="19" r="6" fill="#febc2e"/>'
          '<circle cx="62" cy="19" r="6" fill="#28c840"/>')


def esc(value):
    return escape(str(value), quote=True)


def freeze_opacity(begin, value="1"):
    """Pin opacity at `begin` seconds; pair with <g opacity="0"> to fade in."""
    return (f'<set attributeName="opacity" to="{value}" '
            f'begin="{max(begin, 0):.2f}s" fill="freeze"/>')


def linear_gradient(gid, stops, x1=0, y1=0, x2=0, y2=1):
    body = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return (f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" '
            f'x2="{x2}" y2="{y2}">{body}</linearGradient>')


def window_frame(width, height, title, *, bar_h=38, radius=12,
                 bg="url(#bg)", stroke="#263042", bar_fill="#151c2a",
                 title_fill="#7d86a8", title_size=13):
    """Rounded panel with a title bar and three traffic lights."""
    return "\n  ".join([
        f'<rect width="{width}" height="{height}" rx="{radius}" fill="{bg}" '
        f'stroke="{stroke}"/>',
        # second rect squares off the bottom corners of the title bar
        f'<rect width="{width}" height="{bar_h}" rx="{radius}" fill="{bar_fill}"/>',
        f'<rect y="{bar_h - radius}" width="{width}" height="{radius}" fill="{bar_fill}"/>',
        LIGHTS,
        f'<text x="{width / 2}" y="{bar_h / 2 + 5}" text-anchor="middle" '
        f'fill="{title_fill}" font-size="{title_size}">{esc(title)}</text>',
    ])


def typed_command(index, x, y, text, begin, *, prompt="\u276f ", char_w=8.6,
                  line_h=24, seconds_per_char=0.07, prompt_fill="#7ee787",
                  text_fill="#e6edf3"):
    """Typewriter line: a clip rect that widens one character at a time.

    Uses calcMode="discrete" + per-character keyTimes, so the cost is O(1)
    elements per line instead of one <set> per character.
    """
    n = len(text)
    dur = max(n * seconds_per_char, 0.2)
    key_times = ";".join(f"{k / (n + 1):.4f}" for k in range(n + 1))
    values = ";".join(f"{(len(prompt) + k) * char_w + 4:.1f}" for k in range(n + 1))
    clip_id = f"clip-{index}"
    return (f'  <clipPath id="{clip_id}"><rect x="{x}" y="{y - 16}" height="{line_h}" '
            f'width="{len(prompt) * char_w:.1f}">'
            f'<animate attributeName="width" begin="{begin:.2f}s" dur="{dur:.2f}s" '
            f'fill="freeze" calcMode="discrete" keyTimes="{key_times}" '
            f'values="{values}"/></rect></clipPath>\n'
            f'  <g opacity="0">{freeze_opacity(begin - 0.3)}\n'
            f'    <text x="{x}" y="{y}" clip-path="url(#{clip_id})">'
            f'<tspan fill="{prompt_fill}">{esc(prompt)}</tspan>'
            f'<tspan fill="{text_fill}">{esc(text)}</tspan></text>\n'
            f'  </g>', dur)


def blink_cursor(x, y, *, width=8, height=16, fill="#e6edf3"):
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}">'
            '<animate attributeName="opacity" values="1;1;0;0" '
            'keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect>')


def smooth_width(x, y, track_w, ratio, color, begin, *, height=8, radius=4):
    """A bar that grows from 0 to `ratio * track_w` with an ease-out curve."""
    return (f'<rect x="{x}" y="{y}" width="0" height="{height}" rx="{radius}" fill="{color}">'
            f'<animate attributeName="width" from="0" to="{track_w * ratio:.1f}" '
            f'begin="{begin:.2f}s" dur="1.2s" fill="freeze" calcMode="spline" '
            f'keySplines="0.2 0.8 0.2 1" keyTimes="0;1"/></rect>')
