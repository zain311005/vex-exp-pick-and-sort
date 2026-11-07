"""Write the parts of the docs that come from the code.

    python3 tools/make_docs.py          write docs/CONFIG.md, docs/wiring.svg and docs/flow.svg
    python3 tools/make_docs.py --check  exit 1 if any of them is out of date

docs/CONFIG.md lists every setting in config/settings.py with its comment.
docs/wiring.svg shows which Smart Port each motor and sensor uses, so it
always matches the settings. docs/flow.svg shows the states of the sort.
Laptop only. Needs nothing beyond the Python standard library.
"""

import ast
import io
import math
import os
import re
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, "config")
if CONFIG not in sys.path:
    sys.path.insert(0, CONFIG)

import settings  # noqa: E402

SETTINGS_FILE = os.path.join(CONFIG, "settings.py")
CONFIG_DOC = os.path.join(ROOT, "docs", "CONFIG.md")
WIRING_SVG = os.path.join(ROOT, "docs", "wiring.svg")
FLOW_SVG = os.path.join(ROOT, "docs", "flow.svg")
SECTION = re.compile(r"^# -{3,} (.+)$")
FIRST_TOKEN = re.compile(r'^("[^"]*"|\([^)]*\))\s+(.*)$')
LONG_VALUE = 60


# ---------------------------------------------------------- settings doc
def _comment_text(line):
    """(indent, text) of a full-line comment such as '#   "path"  drive it'."""
    body = line.strip()[1:]
    return len(body) - len(body.lstrip(" ")), body.strip()


def read_settings():
    """[(title, note lines, [(name, value, notes)])] for each section of settings.py.

    A comment block straight after a section heading describes the section.
    A block that ends with a blank line does too. A block that sits directly
    on top of a setting, a comment at the end of its line, and comments
    inside a value that spans several lines all describe that setting.
    """
    with open(SETTINGS_FILE) as handle:
        source = handle.read()
    lines = source.split("\n")
    trailing = {}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT and lines[tok.start[0] - 1][:tok.start[1]].strip():
            trailing[tok.start[0]] = tok.string[1:].strip()
    starts = {}
    inside = set()
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            starts[node.lineno] = node
            inside.update(range(node.lineno + 1, node.end_lineno + 1))

    sections = []
    block = []
    after_heading = False
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        heading = SECTION.match(stripped)
        if heading:
            sections.append((heading.group(1).strip(), [], []))
            block = []
            after_heading = True
        elif number in starts:
            node = starts[number]
            notes = []
            if after_heading:
                sections[-1][1].extend(block)
            elif block:
                notes.append(" ".join(text for indent, text in block))
            block = []
            after_heading = False
            if number in trailing:
                notes.append(trailing[number])
            inner = [_comment_text(lines[n - 1])[1] for n in range(number + 1, node.end_lineno + 1)
                     if lines[n - 1].strip().startswith("#")]
            inner += [trailing[n] for n in range(number + 1, node.end_lineno + 1) if n in trailing]
            if inner:
                notes.append(" ".join(inner))
            value = " ".join(ast.get_source_segment(source, node.value).split())
            if sections:
                note = " ".join(_sentence(fragment) for fragment in notes)
                sections[-1][2].append((node.targets[0].id, value, note))
        elif number in inside:
            continue
        elif stripped.startswith("#"):
            block.append(_comment_text(line))
        else:
            if block and sections:
                sections[-1][1].extend(block)
            block = []
            after_heading = False
    return sections


def _sentence(text):
    """A comment fragment as a sentence: capital first letter, full stop."""
    text = text.strip()
    if text[:1].islower():
        text = text[0].upper() + text[1:]
    if text and text[-1] not in ".!?:":
        text += "."
    return text


def _cell(text):
    return text.replace("|", "\\|")


def _note_markdown(lines):
    """Comment lines as Markdown: paragraphs, and bullets for indented lines."""
    out = []
    paragraph = []
    bullet = None
    bullet_indent = 0

    def flush():
        if paragraph:
            out.append(" ".join(paragraph))
            out.append("")
            del paragraph[:]

    for indent, text in lines:
        if indent >= 2 and bullet is not None and indent > bullet_indent + 2:
            bullet.append(text)
        elif indent >= 2:
            flush()
            bullet = [text]
            bullet_indent = indent
            out.append(bullet)
        else:
            bullet = None
            if out and isinstance(out[-1], list):
                out.append("")
            paragraph.append(text)
    flush()
    rendered = []
    for item in out:
        if isinstance(item, list):
            text = " ".join(" ".join(item).split())
            match = FIRST_TOKEN.match(text)
            if match:
                text = "`%s` %s" % (match.group(1), match.group(2))
            rendered.append("- " + text)
        else:
            rendered.append(item)
    while rendered and rendered[-1] == "":
        rendered.pop()
    return rendered


def config_markdown():
    out = [
        "# Settings reference",
        "",
        "Generated from `config/settings.py` by `tools/make_docs.py`. Do not edit",
        "this file: change the comments in `settings.py` and run the script again.",
        "Values marked MEASURE are estimates to check on your own robot, and",
        "[ASSUMPTIONS.md](ASSUMPTIONS.md) says where each value came from.",
        "",
    ]
    for title, notes, entries in read_settings():
        out.append("## " + title)
        out.append("")
        if notes:
            out.extend(_note_markdown(notes))
            out.append("")
        out.append("| Setting | Value | Notes |")
        out.append("|---|---|---|")
        for name, value, note in entries:
            if len(value) > LONG_VALUE:
                shown = "see `config/settings.py`"
            else:
                shown = "`%s`" % value
            out.append("| `%s` | %s | %s |" % (name, _cell(shown), _cell(note)))
        out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------- SVG
FONT = 'font-family="Helvetica, Arial, sans-serif"'


def _esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rect(x, y, w, h, fill="#ffffff", stroke="#333333", dash=False, rx=6):
    extra = ' stroke-dasharray="6 4"' if dash else ""
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s"'
            ' stroke-width="1.5"%s/>' % (x, y, w, h, rx, fill, stroke, extra))


def _text(x, y, text, size=13, anchor="start", bold=False, colour="#222222"):
    weight = ' font-weight="bold"' if bold else ""
    return ('<text x="%g" y="%g" %s font-size="%g" text-anchor="%s" fill="%s"%s>%s</text>'
            % (x, y, FONT, size, anchor, colour, weight, _esc(text)))


def _lines(x, y, lines, size=13, anchor="start", bold_first=False, gap=None):
    gap = gap or size * 1.3
    out = []
    for i, line in enumerate(lines):
        out.append(_text(x, y + i * gap, line, size, anchor, bold_first and i == 0))
    return out


def _arrow(points, dash=False, colour="#333333", head=9.0):
    """A line through points with a filled arrowhead at the last one.

    The head is drawn as a triangle rather than an SVG marker, so it shows
    the same in a browser and in the PDF.
    """
    (x1, y1), (x2, y2) = points[-2], points[-1]
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    bx, by = x2 - ux * head, y2 - uy * head
    px, py = -uy * head * 0.5, ux * head * 0.5
    line = list(points[:-1]) + [(bx, by)]
    extra = ' stroke-dasharray="6 4"' if dash else ""
    path = " ".join(("M" if i == 0 else "L") + " %.1f %.1f" % p for i, p in enumerate(line))
    tip = "%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (x2, y2, bx + px, by + py, bx - px, by - py)
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="1.5"%s/>\n'
            '<polygon points="%s" fill="%s"/>' % (path, colour, extra, tip, colour))


def _svg(width, height, parts):
    head = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
        % (width, height, width, height),
        '<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>' % (width, height),
    ]
    return "\n".join(head + parts + ["</svg>", ""])


# What each device is, where it goes and where it faces: (setting, name,
# where on the robot, facing, marker position on the top view sketch).
DEVICES = [
    ("OPTICAL_PORT", "Optical Sensor", "claw palm, at ball height", "into the claw", (778, 196)),
    ("ARM_PORT", "Arm motor", "on the tower, drives the arm gear", "-", (805, 300)),
    ("CLAW_PORT", "Claw motor", "on the claw", "-", (860, 150)),
    ("DISTANCE_PORT", "Distance Sensor", "front centre, about 50 mm up", "forward", (832, 222)),
    ("LEFT_DRIVE_PORT", "Left drive motor", "left side, turns the traction wheel", "-", (742, 420)),
    ("RIGHT_DRIVE_PORT", "Right drive motor", "right side, turns the traction wheel", "-", (868, 420)),
]


def wiring_svg():
    ports = dict((name, getattr(settings, name)) for name, _, _, _, _ in DEVICES)
    used = dict((port, name) for name, port in ports.items())
    devices = sorted(DEVICES, key=lambda device: ports[device[0]])
    parts = [_text(30, 38, "Clawbot wiring: which Smart Port each motor and sensor uses",
                   18, bold=True)]

    # the Brain and its ten ports
    parts.append(_rect(30, 60, 220, 500, "#f2f2f2"))
    parts.append(_text(140, 88, "EXP Brain", 15, "middle", True))
    port_y = {}
    for port in range(1, 11):
        y = 104 + (port - 1) * 44
        port_y[port] = y + 17
        if port in used:
            parts.append(_rect(50, y, 180, 34, "#dce9f5", "#2b5d8a", rx=4))
            parts.append(_text(62, y + 22, "Port %d" % port, 13, bold=True))
        else:
            parts.append(_rect(50, y, 180, 34, "#ffffff", "#aaaaaa", dash=True, rx=4))
            parts.append(_text(62, y + 22, "Port %d   free" % port, 13, colour="#888888"))

    # one box per device, joined to its port
    for i, (name, label, where, facing, marker) in enumerate(devices):
        y = 70 + i * 82
        port = ports[name]
        parts.append(_arrow([(230, port_y[port]), (330, y + 33)]))
        parts.append(_rect(330, y, 310, 66, "#ffffff", "#2b5d8a"))
        parts.append(_text(344, y + 21, "%s (port %d)" % (label, port), 14, bold=True))
        parts.append(_text(344, y + 39, "%s = %d" % (name, port), 12, colour="#2b5d8a"))
        detail = where if facing == "-" else "%s, facing %s" % (where, facing)
        parts.append(_text(344, y + 56, detail, 12))

    # top view sketch
    parts.append(_text(805, 74, "Top view sketch, not to scale", 13, "middle", True))
    parts.append(_text(805, 96, "front (claw end)", 12, "middle"))
    parts.append(_arrow([(805, 118), (805, 104)]))
    parts.append(_rect(722, 200, 166, 262, "#f7f7f7", rx=8))
    parts.append(_rect(758, 120, 18, 84, "#ffffff", rx=3))
    parts.append(_rect(834, 120, 18, 84, "#ffffff", rx=3))
    parts.append('<line x1="758" y1="204" x2="852" y2="204" stroke="#333333" stroke-width="3"/>')
    for x in (700, 888):
        parts.append(_rect(x, 214, 22, 56, "#e6e6e6", rx=3))
        parts.append(_rect(x, 392, 22, 56, "#bbbbbb", rx=3))
    parts.append(_text(805, 488, "omni wheels at the front,", 11, "middle"))
    parts.append(_text(805, 502, "driven traction wheels at the back", 11, "middle"))
    parts.append(_rect(778, 360, 54, 30, "#dce9f5", "#2b5d8a", rx=3))
    parts.append(_text(805, 380, "Brain", 11, "middle"))
    for name, label, where, facing, (x, y) in DEVICES:
        parts.append('<circle cx="%g" cy="%g" r="12" fill="#2b5d8a"/>' % (x, y))
        parts.append(_text(x, y + 4.5, str(ports[name]), 12, "middle", True, "#ffffff"))
    parts.extend(_lines(700, 530, [
        "Numbers are Smart Ports. Build the robot from",
        "the official EXP Clawbot instructions: this",
        "sketch only shows where each cable goes.",
    ], 11))
    return _svg(960, 590, parts)


def flow_svg():
    parts = [_text(30, 36, "The sort, state by state (RUN_MODE \"sort\")", 18, bold=True)]
    parts.append(_rect(250, 54, 400, 50, "#f2f2f2"))
    parts.extend(_lines(450, 74, ["Start: calibrate the gyro, wait for CHECK,",
                                  "home the arm and the claw"], 13, "middle"))
    states = ["FOLLOW_PATH", "APPROACH", "GRAB", "CLASSIFY", "GO_TO_BOX", "RELEASE", "RETURN"]
    tops = {}
    for i, name in enumerate(states):
        y = 130 + i * 92
        tops[name] = y
        parts.append(_rect(330, y, 240, 48, "#dce9f5", "#2b5d8a"))
        parts.append(_text(450, y + 30, name, 15, "middle", True))
    parts.append(_arrow([(450, 104), (450, tops["FOLLOW_PATH"])]))
    labels = {
        "FOLLOW_PATH": ["ball seen on the board"],
        "APPROACH": ["ball in the claw"],
        "GRAB": ["holding it"],
        "CLASSIFY": ["known colour: its box", "unknown: the reject spot"],
        "GO_TO_BOX": ["ball over the box"],
        "RELEASE": ["claw empty"],
    }
    for name, nxt in zip(states, states[1:]):
        parts.append(_arrow([(450, tops[name] + 48), (450, tops[nxt])]))
        parts.extend(_lines(462, tops[name] + 66, labels[name], 12))
    back = tops["RETURN"] + 24
    parts.append(_arrow([(330, back), (296, back), (296, tops["FOLLOW_PATH"] + 24),
                         (330, tops["FOLLOW_PATH"] + 24)]))
    parts.extend(_lines(288, back - 40, ["back on", "the path"], 12, "end"))

    # finished
    parts.append(_rect(650, tops["FOLLOW_PATH"], 210, 48, "#e8f4e8", "#3c763d"))
    parts.extend(_lines(755, tops["FOLLOW_PATH"] + 20, ["SORT DONE", "path finished"], 13,
                        "middle", True))
    parts.append(_arrow([(570, tops["FOLLOW_PATH"] + 24), (650, tops["FOLLOW_PATH"] + 24)]))

    # giving up on a spot
    give_up = tops["APPROACH"] + 4
    parts.append(_rect(650, give_up, 210, 112, "#fff6e5", "#a66b00"))
    parts.extend(_lines(664, give_up + 22, ["Give up on this spot", "lost, too far, never in",
                                            "the claw, or grip failed",
                                            "twice. Ignore it from now",
                                            "on and go back to the path"], 12, bold_first=True))
    parts.append(_arrow([(570, tops["APPROACH"] + 24), (650, give_up + 30)]))
    parts.append(_arrow([(570, tops["GRAB"] + 24), (650, give_up + 90)]))
    parts.append(_arrow([(860, give_up + 56), (884, give_up + 56), (884, tops["RETURN"] + 24),
                         (570, tops["RETURN"] + 24)], dash=True))

    # stopping with a message
    stop_top = tops["GO_TO_BOX"] - 18
    parts.append(_rect(650, stop_top, 210, 112, "#fbeaea", "#a94442"))
    parts.extend(_lines(664, stop_top + 22, ["SORT STOPPED", "a time limit ran out, a",
                                             "drive was stuck, or a ball",
                                             "stuck in the claw: every",
                                             "motor stops, screen says why"], 12, bold_first=True))
    parts.append(_arrow([(570, tops["GO_TO_BOX"] + 24), (650, stop_top + 60)], dash=True))
    parts.extend(_lines(664, stop_top + 132, ["(from any state)"], 12))

    # something in the way
    blocked_top = tops["GRAB"] - 10
    parts.append(_rect(20, blocked_top, 240, 112, "#fff6e5", "#a66b00"))
    parts.extend(_lines(34, blocked_top + 22, ["Something in the way", "nearer than 150 mm and",
                                               "not a ball to fetch: stop,",
                                               "ask for it to be cleared,",
                                               "carry on after CHECK"], 12, bold_first=True))
    parts.append(_arrow([(330, tops["FOLLOW_PATH"] + 40), (200, blocked_top)], dash=True))
    parts.extend(_lines(34, blocked_top + 132, ["(also on the way to a", "box and back)"], 12))

    parts.append(_text(450, 806, "Left or Right button on the Brain: everything stops, "
                                 "from any state.", 13, "middle", True))
    return _svg(900, 830, parts)


# ---------------------------------------------------------------- main
def outputs():
    return [(CONFIG_DOC, config_markdown() + "\n"), (WIRING_SVG, wiring_svg()),
            (FLOW_SVG, flow_svg())]


def main(argv):
    if "--check" in argv:
        stale = []
        for path, wanted in outputs():
            current = None
            if os.path.exists(path):
                with open(path) as handle:
                    current = handle.read()
            if current != wanted:
                stale.append(os.path.relpath(path, ROOT))
        if stale:
            print("out of date: %s. Run: python3 tools/make_docs.py" % ", ".join(stale))
            return 1
        print("generated docs are up to date.")
        return 0
    for path, wanted in outputs():
        with open(path, "w") as handle:
            handle.write(wanted)
        print("wrote %s" % os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
