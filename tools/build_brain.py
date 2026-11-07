"""Build brain/clawbot.py, the single file that runs on the EXP Brain.

A VEXcode EXP Python project is one file, so this script joins
config/settings.py and the modules in src/ into brain/clawbot.py.

    python3 tools/build_brain.py          write brain/clawbot.py and clawbot_compact.py
    python3 tools/build_brain.py --check  exit 1 if either is out of date

brain/clawbot_compact.py is the same program with the comments and
docstrings taken out, in case the full file is too big for the Brain.

The build refuses code that MicroPython 1.13 (Python 3.4 syntax, the version
VEX lists for the EXP Brain) cannot run, and any import other than vex and
math. It needs Python 3.9 or newer on the laptop. Laptop only: this script
never goes onto the Brain.
"""

import ast
import io
import os
import sys
import tokenize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "brain", "clawbot.py")
COMPACT_OUTPUT = os.path.join(ROOT, "brain", "clawbot_compact.py")

# Order matters: each part may only use names defined in the parts above it.
PARTS = [
    "config/settings.py",
    "src/geometry.py",
    "src/paths.py",
    "src/hardware.py",
    "src/robot.py",
    "src/distance.py",
    "src/colour.py",
    "src/arm.py",
    "src/mission.py",
    "src/bringup.py",
    "src/main.py",
]
PROJECT_MODULES = {"settings", "geometry", "paths", "hardware", "robot", "distance",
                   "colour", "arm", "mission", "bringup", "main"}
BRAIN_MODULES = ["vex", "math"]

HEADER = """# clawbot.py
#
# GENERATED FILE - do not edit by hand.
# Built by tools/build_brain.py from config/settings.py and src/*.py.
# To change a setting, edit config/settings.py and run the build again.
#
# To use: create a new VEXcode EXP Python project, delete the template
# code, paste in this whole file, and download it to the Brain.
#
# UNTESTED ON HARDWARE. This file has only been run in the simulator and
# against a fake vex module. Work through docs/BRINGUP.md before trusting
# it on a robot, and keep a hand near the Brain's stop buttons.
"""


COMPACT_HEADER = """# clawbot_compact.py
#
# GENERATED FILE - do not edit by hand. The same program as clawbot.py with
# the comments and docstrings taken out, in case the full file is too big
# for the Brain. Built by tools/build_brain.py. UNTESTED ON HARDWARE.
"""


class BuildError(Exception):
    pass


def _is_vex_import_guard(node):
    """The try: from vex import * / except ImportError block in hardware.py."""
    if not isinstance(node, ast.Try) or len(node.body) != 1:
        return False
    inner = node.body[0]
    return isinstance(inner, ast.ImportFrom) and inner.module == "vex"


def _strip_imports(path, source):
    """Remove module-level imports. Returns (body, brain_modules_used)."""
    tree = ast.parse(source, filename=path)
    drop = set()
    used = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name in BRAIN_MODULES:
                    used.add(name)
                elif name not in PROJECT_MODULES:
                    raise BuildError("%s:%d imports %s, which the Brain does not have"
                                     % (path, node.lineno, alias.name))
            drop.update(range(node.lineno, node.end_lineno + 1))
        elif isinstance(node, ast.ImportFrom):
            name = (node.module or "").split(".")[0]
            if name in BRAIN_MODULES:
                used.add(name)
            elif name not in PROJECT_MODULES:
                raise BuildError("%s:%d imports from %s, which the Brain does not have"
                                 % (path, node.lineno, node.module))
            drop.update(range(node.lineno, node.end_lineno + 1))
        elif _is_vex_import_guard(node):
            used.add("vex")
            drop.update(range(node.lineno, node.end_lineno + 1))
    lines = source.splitlines()
    kept = [line for number, line in enumerate(lines, start=1) if number not in drop]
    while kept and not kept[0].strip():
        kept.pop(0)
    return "\n".join(kept).rstrip() + "\n", used


def _top_level_names(path, source):
    names = []
    for node in ast.parse(source, filename=path).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                for item in ast.walk(target):
                    if isinstance(item, ast.Name):
                        names.append(item.id)
    return names


def micropython_problems(source, filename="<brain>"):
    """Syntax the EXP Brain's MicroPython 1.13 (Python 3.4) cannot run."""
    problems = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        line = getattr(node, "lineno", "?")
        if isinstance(node, ast.JoinedStr):
            problems.append("line %s: f-string (Python 3.6)" % line)
        elif isinstance(node, ast.AnnAssign):
            problems.append("line %s: variable annotation (Python 3.6)" % line)
        elif isinstance(node, ast.NamedExpr):
            problems.append("line %s: := operator (Python 3.8)" % line)
        elif isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith, ast.Await)):
            problems.append("line %s: async/await (Python 3.5)" % line)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult):
            problems.append("line %s: @ operator (Python 3.5)" % line)
        elif isinstance(node, ast.Set) or (isinstance(node, (ast.List, ast.Tuple))
                                           and isinstance(node.ctx, ast.Load)):
            # a, *rest = items is fine in 3.4; [*a, *b] is not
            if any(isinstance(item, ast.Starred) for item in node.elts):
                problems.append("line %s: * unpacking inside a literal (Python 3.5)" % line)
        elif isinstance(node, ast.Call):
            starred = [i for i, arg in enumerate(node.args) if isinstance(arg, ast.Starred)]
            if len(starred) > 1 or (starred and starred[0] != len(node.args) - 1):
                problems.append("line %s: * unpacking not at the end of a call (Python 3.5)" % line)
            names = [keyword.arg for keyword in node.keywords]
            if None in names and (names.count(None) > 1 or names[-1] is not None):
                problems.append("line %s: ** unpacking not at the end of a call (Python 3.5)" % line)
        elif isinstance(node, ast.Dict):
            if any(key is None for key in node.keys):
                problems.append("line %s: ** unpacking inside a dict (Python 3.5)" % line)
        elif isinstance(node, (ast.FunctionDef, ast.Lambda)):
            args = node.args
            if args.posonlyargs:
                problems.append("line %s: positional-only parameters (Python 3.8)" % line)
            if isinstance(node, ast.FunctionDef) and node.returns is not None:
                problems.append("line %s: return annotation" % line)
            for arg in args.posonlyargs + args.args + args.kwonlyargs:
                if arg.annotation is not None:
                    problems.append("line %s: parameter annotation" % line)
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.NUMBER and "_" in tok.string:
            problems.append("line %d: underscore in a number (Python 3.6)" % tok.start[0])
    return problems


def build():
    """Return the text of brain/clawbot.py built from the current sources."""
    used = set()
    seen = {}
    sections = []
    for part in PARTS:
        with open(os.path.join(ROOT, part)) as handle:
            source = handle.read()
        for name in _top_level_names(part, source):
            if name in seen and seen[name] != part:
                raise BuildError("%s is defined in both %s and %s" % (name, seen[name], part))
            seen[name] = part
        body, part_used = _strip_imports(part, source)
        used.update(part_used)
        bar = "# " + "=" * 72
        sections.append("%s\n# from %s\n%s\n\n%s" % (bar, part, bar, body))
    imports = []
    if "vex" in used:
        imports.append("from vex import *")
    if "math" in used:
        imports.append("import math")
    text = HEADER + "\n" + "\n".join(imports) + "\n\n\n" + "\n\n".join(sections) + "\n\nmain()\n"
    problems = micropython_problems(text, OUTPUT)
    if problems:
        raise BuildError("brain file would not run on the EXP Brain:\n  " + "\n  ".join(problems))
    compile(text, OUTPUT, "exec")
    return text


def compact(text):
    """The Brain file without its comments, docstrings and blank lines."""
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body.pop(0)
                if not body:
                    body.append(ast.Pass())
    out = COMPACT_HEADER + "\n" + ast.unparse(tree) + "\n"
    problems = micropython_problems(out, COMPACT_OUTPUT)
    if problems:
        raise BuildError("compact file would not run on the EXP Brain:\n  " + "\n  ".join(problems))
    compile(out, COMPACT_OUTPUT, "exec")
    return out


def main(argv):
    text = build()
    outputs = [(OUTPUT, text), (COMPACT_OUTPUT, compact(text))]
    if "--check" in argv:
        stale = []
        for path, wanted in outputs:
            current = ""
            if os.path.exists(path):
                with open(path) as handle:
                    current = handle.read()
            if current != wanted:
                stale.append(os.path.relpath(path, ROOT))
        if stale:
            print("out of date: %s. Run: python3 tools/build_brain.py" % ", ".join(stale))
            return 1
        print("brain files are up to date.")
        return 0
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    for path, wanted in outputs:
        with open(path, "w") as handle:
            handle.write(wanted)
        print("wrote %s (%d lines, %d bytes)"
              % (os.path.relpath(path, ROOT), wanted.count("\n"), len(wanted)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
