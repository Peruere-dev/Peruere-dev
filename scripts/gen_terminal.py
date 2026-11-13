"""Animated terminal (820 wide) that types a shell session from the config.

`cmd` lines are typed out character by character, `out` / `err` lines appear
as whole lines. The cursor keeps blinking when the session ends.
"""
import svg_kit as kit

W, TOP, LEFT, LINE_H = 820, 62, 26, 24
CHAR_W = 8.6          # width of a 14px monospace glyph, calibrated for the
                      # font stack in svg_kit.MONO -- edit if you swap fonts
TYPE_SPEED = 0.07     # seconds per character
PAUSE = 0.45
COLORS = {"out": "#a5b1d6", "err": "#ff7b72"}


def _width(script):
    return TOP + LINE_H * (len(script) + 1) + 10


def render(cfg):
    script = [tuple(line) for line in cfg["terminal"]["script"]]
    height = _width(script)
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{height}" viewBox="0 0 {W} {height}" font-family="{kit.MONO}" font-size="14">
  <defs>
    {kit.linear_gradient("bg", [(0, "#0f1320"), (1, "#171b2e")], 0, 0, 1, 1)}
  </defs>
  {kit.window_frame(W, height, cfg["terminal"]["title"], bar_h=36, bar_fill="#1c2136", stroke="#2b3150")}''']

    now = 0.6
    y = TOP
    for index, (kind, text) in enumerate(script):
        if kind == "cmd":
            markup, dur = kit.typed_command(
                index, LEFT, y, text, now, char_w=CHAR_W, line_h=LINE_H,
                seconds_per_char=TYPE_SPEED)
            parts.append(markup)
            now += dur + PAUSE
        else:
            color = COLORS.get(kind, COLORS["out"])
            parts.append(
                f'  <text x="{LEFT}" y="{y}" fill="{color}" opacity="0" '
                f'xml:space="preserve">{kit.esc(text)}{kit.freeze_opacity(now)}</text>')
            following = script[index + 1:index + 2]
            now += 0.25 if following and following[0][0] != "cmd" else PAUSE + 0.2
        y += LINE_H

    parts.append(
        f'  <g opacity="0">{kit.freeze_opacity(now)}\n'
        f'    <text x="{LEFT}" y="{y}" fill="#7ee787">\u276f</text>\n'
        f'    {kit.blink_cursor(LEFT + 2 * CHAR_W, y - 13)}\n'
        f'  </g>\n</svg>')
    return "\n".join(parts) + "\n"


def generate(cfg, path):
    path.write_text(render(cfg), encoding="utf-8")
    return path
