import glob
import os
import re
import subprocess
import tempfile

import pytest

import make_docs
import settings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKDOWN = ["README.md"] + sorted(os.path.relpath(path, ROOT)
                                  for path in glob.glob(os.path.join(ROOT, "docs", "*.md")))
SKIP_FOLDERS = {".git", "__pycache__", ".pytest_cache", "out", ".venv", "venv"}
TEXT_ENDINGS = (".py", ".md", ".svg", ".csv", ".txt", ".ini", ".gitignore")

README_SECTIONS = [
    "What it does", "How it works", "Parts list", "Wiring", "Setup", "Calibration",
    "Running it", "Changing the path", "Config reference", "Simulator and tests",
    "Troubleshooting", "Limitations", "Safety", "Licence and credits",
    "Not affiliated with VEX",
]
HYPE_WORDS = [
    "seamless", "robust", "powerful", "cutting-edge", "cutting edge", "state-of-the-art",
    "revolutionary", "game-changer", "game changer", "effortless", "leverage", "elevate",
    "unleash", "supercharge", "blazing", "world-class", "best-in-class", "next-generation",
    "groundbreaking", "innovative", "intelligent", "magic",
]
LONG_DASHES = {chr(0x2014), chr(0x2013)}     # em dash and en dash
# figures that came from a VEX page, so they need a link to it nearby
RANGE_FIGURES = ["2000 mm", "0 to 359", "32 GB", "MicroPython 1.13"]


def read(path):
    with open(os.path.join(ROOT, path)) as handle:
        return handle.read()


def text_files():
    for folder, subfolders, files in os.walk(ROOT):
        subfolders[:] = [name for name in subfolders if name not in SKIP_FOLDERS]
        for name in files:
            if name.endswith(TEXT_ENDINGS):
                yield os.path.relpath(os.path.join(folder, name), ROOT)


def paragraphs(text):
    return [block for block in re.split(r"\n\s*\n", text) if block.strip()]


# --------------------------------------------------------------- README
def test_readme_has_every_section():
    headings = re.findall(r"^## (.+)$", read("README.md"), re.M)
    for section in README_SECTIONS:
        assert section in headings, section


def test_readme_says_it_is_untested_and_not_affiliated():
    readme = " ".join(read("README.md").split())
    assert "UNTESTED ON HARDWARE" in readme
    assert "not affiliated with or endorsed by VEX Robotics" in readme


def test_wiring_table_matches_the_settings():
    readme = read("README.md")
    section = readme.split("## Wiring", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| `([A-Z_]+_PORT)` \| (\d+) \|", section, re.M)
    names = [name for name in dir(settings) if name.endswith("_PORT")]
    assert sorted(name for name, port in rows) == sorted(names)
    for name, port in rows:
        assert getattr(settings, name) == int(port), name


def test_range_figures_in_the_readme_come_with_an_official_link():
    for block in paragraphs(read("README.md")):
        if any(figure in block for figure in RANGE_FIGURES):
            assert "](https://api.vex.com/" in block, block[:80]


# ----------------------------------------------------------- all docs
def test_no_long_dashes_anywhere():
    for path in text_files():
        text = read(path)
        assert LONG_DASHES.isdisjoint(text), path


@pytest.mark.parametrize("path", MARKDOWN)
def test_no_hype_words(path):
    text = read(path).lower()
    for word in HYPE_WORDS:
        assert not re.search(r"\b%s\b" % re.escape(word), text), (path, word)


@pytest.mark.parametrize("path", MARKDOWN)
def test_links_go_somewhere_real(path):
    text = read(path)
    folder = os.path.dirname(os.path.join(ROOT, path))
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith("http"):
            assert target.startswith("https://"), target
        elif not target.startswith("#"):
            assert os.path.exists(os.path.join(folder, target.split("#")[0])), (path, target)


@pytest.mark.parametrize("path", MARKDOWN)
def test_docs_only_use_characters_the_pdf_fonts_have(path):
    read(path).encode("cp1252")


def test_vex_links_point_at_vex():
    text = read("docs/REFERENCES.md")
    for url in re.findall(r"\]\((https://[^)]+)\)", text):
        host = url.split("/")[2]
        assert host.endswith(("vex.com", "vexrobotics.com")), url


# ------------------------------------------------------ generated files
def test_generated_docs_are_up_to_date():
    for path, wanted in make_docs.outputs():
        with open(path) as handle:
            assert handle.read() == wanted, "run: python3 tools/make_docs.py"


def test_every_setting_is_in_the_config_reference():
    reference = read("docs/CONFIG.md")
    for name in dir(settings):
        if name.isupper():
            assert "`%s`" % name in reference, name


def test_wiring_diagram_shows_every_port():
    svg = read("docs/wiring.svg")
    for name in dir(settings):
        if name.endswith("_PORT"):
            assert "%s = %d" % (name, getattr(settings, name)) in svg, name


def test_guide_pdf_is_up_to_date():
    pytest.importorskip("reportlab")
    pytest.importorskip("svglib")
    import build_guide
    with tempfile.TemporaryDirectory() as folder:
        fresh = os.path.join(folder, "guide.pdf")
        build_guide.build(fresh)
        with open(fresh, "rb") as handle:
            wanted = handle.read()
    with open(build_guide.OUTPUT, "rb") as handle:
        assert handle.read() == wanted, "run: python3 tools/build_guide.py"


# ------------------------------------------------------------- copyright
def tracked_files():
    try:
        listing = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                                 text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git is not available")
    return listing.split()


def test_no_vex_documents_or_images_in_the_repository():
    files = tracked_files()
    pdfs = [path for path in files if path.lower().endswith(".pdf")]
    assert pdfs in ([], ["docs/clawbot-guide.pdf"])
    pictures = [path for path in files
                if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))]
    assert pictures == []
