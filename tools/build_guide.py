"""Build docs/clawbot-guide.pdf from README.md and the files in docs/.

    python3 tools/build_guide.py          write docs/clawbot-guide.pdf
    python3 tools/build_guide.py --check  exit 1 if the PDF is out of date

Needs ReportLab and svglib (pip install -r requirements-dev.txt). It reads
only the small part of Markdown these files use: headings, paragraphs,
lists, tables, code blocks, links, bold, inline code and SVG images. The
output is the same byte for byte each time, so a test can tell when the
PDF needs building again. Laptop only.
"""

import os
import re
import sys

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer,
                                Table, TableStyle)
from svglib.svglib import svg2rlg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT = os.path.join(ROOT, "docs", "clawbot-guide.pdf")
PARTS = ["README.md", "docs/BRINGUP.md", "docs/ASSUMPTIONS.md", "docs/CONFIG.md",
         "docs/REFERENCES.md"]
TITLE = "vex-exp-pick-and-sort guide"
LINK_COLOUR = "#1f4e79"
MARGIN = 18 * mm
WIDTH = A4[0] - 2 * MARGIN

INLINE = re.compile(r"(`[^`]+`)|(\*\*.+?\*\*)|(\[[^\]]+\]\([^)]+\))")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ITEM = re.compile(r"^(\s*)(- \[ \] |- |\d+\. )(.*)$")
IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")


# --------------------------------------------------------------- styles
def make_styles():
    base = getSampleStyleSheet()
    body = ParagraphStyle("body", base["BodyText"], fontName="Helvetica", fontSize=9.5,
                          leading=12.5, spaceAfter=5)
    return {
        "body": body,
        "h1": ParagraphStyle("h1", body, fontName="Helvetica-Bold", fontSize=18, leading=22,
                             spaceBefore=4, spaceAfter=10, keepWithNext=1),
        "h2": ParagraphStyle("h2", body, fontName="Helvetica-Bold", fontSize=13, leading=16,
                             spaceBefore=10, spaceAfter=5, keepWithNext=1),
        "h3": ParagraphStyle("h3", body, fontName="Helvetica-Bold", fontSize=11, leading=14,
                             spaceBefore=8, spaceAfter=4, keepWithNext=1),
        "cell": ParagraphStyle("cell", body, fontSize=8, leading=10, spaceAfter=0),
        "head": ParagraphStyle("head", body, fontName="Helvetica-Bold", fontSize=8, leading=10,
                               spaceAfter=0),
        "code": ParagraphStyle("code", body, fontName="Courier", fontSize=8, leading=10,
                               backColor=colors.HexColor("#f2f2f2"), borderPadding=4,
                               leftIndent=4, spaceBefore=3, spaceAfter=8),
        "caption": ParagraphStyle("caption", body, fontSize=8.5, textColor=colors.HexColor("#555555"),
                                  alignment=TA_CENTER),
        "cover": ParagraphStyle("cover", body, fontName="Helvetica-Bold", fontSize=26, leading=32,
                                alignment=TA_CENTER, spaceAfter=14),
        "centre": ParagraphStyle("centre", body, fontSize=11, leading=15, alignment=TA_CENTER),
    }


# --------------------------------------------------------------- inline
def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text):
    """Markdown inline marks as ReportLab paragraph markup."""
    out = []
    pos = 0
    for match in INLINE.finditer(text):
        out.append(escape(text[pos:match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            out.append('<font face="Courier">%s</font>' % escape(token[1:-1]))
        elif token.startswith("**"):
            out.append("<b>%s</b>" % inline(token[2:-2]))
        else:
            label, url = LINK.match(token).groups()
            if url.startswith("http"):
                out.append('<link href="%s" color="%s">%s</link>'
                           % (escape(url), LINK_COLOUR, inline(label)))
            else:
                out.append(inline(label))   # links between files, shown as plain text
        pos = match.end()
    out.append(escape(text[pos:]))
    return "".join(out)


# --------------------------------------------------------------- blocks
def read_blocks(markdown):
    """The file as a list of blocks: heading, para, list, table, code, image."""
    lines = markdown.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
        elif stripped.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append(("code", "\n".join(code)))
            i += 1
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            blocks.append(("heading", level, line[level:].strip()))
            i += 1
        elif IMAGE.match(stripped):
            alt, path = IMAGE.match(stripped).groups()
            blocks.append(("image", alt, path))
            i += 1
        elif stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", lines[i].strip())[1:-1]]
                if not all(re.match(r"^:?-+:?$", cell) for cell in cells):
                    rows.append([cell.replace("\\|", "|") for cell in cells])
                i += 1
            blocks.append(("table", rows))
        elif ITEM.match(line):
            items = []
            while i < len(lines) and lines[i].strip():
                match = ITEM.match(lines[i])
                if match:
                    level = 1 if len(match.group(1)) >= 2 else 0
                    items.append([level, match.group(2).strip(), match.group(3).strip()])
                elif lines[i].startswith(" "):
                    items[-1][2] += " " + lines[i].strip()
                else:
                    break
                i += 1
            blocks.append(("list", items))
        else:
            text = []
            while (i < len(lines) and lines[i].strip() and not ITEM.match(lines[i])
                   and not lines[i].startswith(("#", "|", "```"))):
                text.append(lines[i].strip())
                i += 1
            blocks.append(("para", " ".join(text)))
    return blocks


def image(path, base, styles, alt):
    drawing = svg2rlg(os.path.join(base, path))
    scale = min(WIDTH / drawing.width, (A4[1] * 0.55) / drawing.height)
    drawing.width *= scale
    drawing.height *= scale
    drawing.scale(scale, scale)
    drawing.hAlign = "CENTER"
    return [drawing, Paragraph(inline(alt), styles["caption"]), Spacer(1, 6)]


def plain(text):
    """Cell text without its Markdown marks, to estimate how wide it is."""
    text = LINK.sub(lambda match: match.group(1), text)
    return text.replace("**", "").replace("`", "")


def column_widths(rows):
    """Give every column room for its longest word, then share out the rest
    in proportion to how much more each column's longest cell wants."""
    columns = len(rows[0])
    char = 4.7      # points per character of 8 point text, roughly
    least = []
    wanted = []
    for c in range(columns):
        cells = [plain(row[c]) if c < len(row) else "" for row in rows]
        words = [len(word) for cell in cells for word in cell.split()] or [1]
        least.append(max(words) * char + 8)
        wanted.append(max(len(cell) for cell in cells) * char + 8)
    if sum(least) >= WIDTH:
        return [width * WIDTH / sum(least) for width in least]
    spare = WIDTH - sum(least)
    extra = [max(want - low, 0.0) for want, low in zip(wanted, least)]
    if not sum(extra):
        return [low + spare / columns for low in least]
    return [low + spare * more / sum(extra) for low, more in zip(least, extra)]


def table(rows, styles):
    header, body = rows[0], rows[1:]
    columns = len(header)
    widths = column_widths(rows)
    data = [[Paragraph(inline(cell), styles["head"]) for cell in header]]
    for row in body:
        row = row + [""] * (columns - len(row))
        data.append([Paragraph(inline(cell), styles["cell"]) for cell in row[:columns]])
    grid = Table(data, colWidths=widths, repeatRows=1)
    grid.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [grid, Spacer(1, 8)]


def flowables(path, styles):
    """Everything in one Markdown file, starting on a new page."""
    with open(os.path.join(ROOT, path)) as handle:
        markdown = handle.read()
    base = os.path.dirname(os.path.join(ROOT, path))
    out = [PageBreak()]
    for block in read_blocks(markdown):
        kind = block[0]
        if kind == "heading":
            out.append(Paragraph(inline(block[2]), styles["h%d" % min(block[1], 3)]))
        elif kind == "para":
            out.append(Paragraph(inline(block[1]), styles["body"]))
        elif kind == "code":
            out.append(Preformatted(block[1], styles["code"]))
        elif kind == "image":
            out.extend(image(block[2], base, styles, block[1]))
        elif kind == "table":
            out.extend(table(block[1], styles))
        elif kind == "list":
            for level, marker, text in block[1]:
                style = ParagraphStyle("item", styles["body"], leftIndent=14 + 14 * level,
                                       bulletIndent=2 + 14 * level, spaceAfter=2)
                bullet = {"-": "-", "- [ ]": "[  ]"}.get(marker, marker)
                if bullet == "-":
                    bullet = "•"
                out.append(Paragraph(inline(text), style, bulletText=bullet))
            out.append(Spacer(1, 4))
    return out


# --------------------------------------------------------------- build
def cover(styles):
    return [
        Spacer(1, 70 * mm),
        Paragraph("vex-exp-pick-and-sort", styles["cover"]),
        Paragraph("A guide to the VEX EXP Clawbot pick-and-sort program", styles["centre"]),
        Spacer(1, 12 * mm),
        Paragraph("<b>UNTESTED ON HARDWARE</b>", styles["centre"]),
        Spacer(1, 30 * mm),
        Paragraph("Contents: README, bring-up checklist, assumptions, settings reference, "
                  "references", styles["centre"]),
        Spacer(1, 6 * mm),
        Paragraph("Built from README.md and the files in docs/ by tools/build_guide.py.",
                  styles["centre"]),
        Paragraph("Not affiliated with or endorsed by VEX Robotics.", styles["centre"]),
    ]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(MARGIN, 10 * mm, TITLE)
    canvas.drawRightString(A4[0] - MARGIN, 10 * mm, "page %d" % doc.page)
    canvas.restoreState()


def build(path):
    rl_config.invariant = 1
    styles = make_styles()
    story = cover(styles)
    for part in PARTS:
        story.extend(flowables(part, styles))
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN + 4 * mm, title=TITLE,
                            author="vex-exp-pick-and-sort", subject=TITLE,
                            creator="tools/build_guide.py")
    doc.build(story, onFirstPage=lambda canvas, doc: None, onLaterPages=footer)


def main(argv):
    if "--check" in argv:
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            fresh = os.path.join(folder, "guide.pdf")
            build(fresh)
            with open(fresh, "rb") as handle:
                wanted = handle.read()
        current = b""
        if os.path.exists(OUTPUT):
            with open(OUTPUT, "rb") as handle:
                current = handle.read()
        if current != wanted:
            print("docs/clawbot-guide.pdf is out of date. Run: python3 tools/build_guide.py")
            return 1
        print("docs/clawbot-guide.pdf is up to date.")
        return 0
    build(OUTPUT)
    print("wrote %s (%d bytes)" % (os.path.relpath(OUTPUT, ROOT), os.path.getsize(OUTPUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
