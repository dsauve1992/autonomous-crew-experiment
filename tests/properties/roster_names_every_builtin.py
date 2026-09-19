"""The Builtins roster in docs/spec.md names every builtin, and only builtins.

Two directions, and the second is the one that needed a machine. A builtin
*removed or renamed* while the document stood still is caught by any program
that calls it, and `tests/cases/builtin_roster.vine` calls all of them. A
builtin *added* and never written down is caught by nothing: tick 14 added
`pow` to REGISTRY, and the hand-written list in that case stayed green until
someone edited it by hand. A roster that is checked in one direction is a
roster that only documents what somebody remembered to document.

So the list is read out of the document rather than copied into this file. It
is `## Builtins` down to the next heading, every backticked `name(` in it --
which is the shape the roster is written in, and the shape it has to keep for
this property to be reading the roster rather than reading nothing. That is
why an empty reading is a failure and not a pass.
"""

import pathlib
import re

from vine.builtins import REGISTRY

CLAIM = "every builtin is named in the Builtins roster of docs/spec.md, and every name in that roster is a builtin"

SPEC = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "spec.md"
# A roster entry is a backticked call: `len(x)`, `range(a, b)`, `print(...)`.
ENTRY = re.compile(r"`([a-z_]+)\(")


def roster():
    """The names the Builtins section lists, in the order it lists them."""
    names = []
    inside = False
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Builtins"
            continue
        if inside:
            for name in ENTRY.findall(line):
                if name not in names:
                    names.append(name)
    return names


def check():
    listed = roster()
    installed = [b.name for b in REGISTRY]
    failures = []
    if not listed:
        failures.append(
            (str(SPEC), "read no names at all from '## Builtins' -- has the section moved or changed shape?")
        )
    for name in installed:
        if name not in listed:
            failures.append((name, "is a builtin and the Builtins roster does not name it"))
    for name in listed:
        if name not in installed:
            failures.append((name, "is named in the Builtins roster and is not a builtin"))
    return len(listed) + len(installed), failures
