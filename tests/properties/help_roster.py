"""The roster in **Errors** names every rule Vine offers, and only those.

A help is a rule of the language -- `docs/spec.md` says so and uses the split
to keep a guess from being printed in the voice of a fact -- so the set of
them is finite, and **The rules a report may offer** writes it out. Twelve.

Both directions, and the second is the one that needed a machine.

- A rule **printed and not listed** is a rule of the language that the
  document does not contain. Nothing could catch it: a help was pinned only by
  the golden of whichever message happened to carry it, and a golden is a copy
  of the message it checks. Tick 24 added the float ceiling to four messages;
  had it invented a thirteenth rule instead, twelve goldens would have been
  amended and nothing would have asked whether the rule was written down.
- A rule **listed and printed by nothing** is a message deleted or reworded
  with the document left behind -- the direction `roster_names_every_builtin`
  was written for, and the one a golden can never reach, because a golden that
  no longer matches any message is a golden that fails for the wrong reason or
  was deleted along with it.

The second side is the *printing*, not `vine/rules.py`. Reading the roster out
of the constants the messages are built from would be one side wearing two
hats: every rule would agree with itself and a rule that reaches no raise site
would look fine. So the rules here are collected by running programs and
reading what came out, and a rule earns its line in the document by being
reachable.

A third clause, about the labels: **no rule in the roster is printed as a
note.** The split is what tells a reader whether a line is about their program
or about the language, and **Errors** draws it at *this failure* against *next
time* -- a note may state the rule that caused the failure, and three do. What
it may never be is one of these twelve, because every one of them would be as
true had the reader made no mistake at all. That is the half of the split a
label check can reach, and nothing else in the suite reaches any of it.

A fourth clause, about the document rather than the language: **every rule is
listed against a section that exists.** Each bullet ends in a bold heading
name, and the reference is only worth writing if it stays true; a section
renamed leaves twelve pointers that read like an answer and are not one. It is
checked separately from the two above and breaks on its own.

The count is exact, for the reason spec_examples_run.py gives: a property that
reads a document has one clause more than it looks, and it is how much it
read. Twelve bullets, and a roster reworded so the parse finds eleven fails
here rather than quietly checking a shorter list.

The programs are `note_and_help_shape.py`'s -- 74,330 from the type grid and
twelve hand-written mistakes. What that reaches, and what it does not, is in
that file's docstring; it reaches all twelve rules, which is the only thing
this property needs of it.
"""

import pathlib
import re

from note_and_help_shape import reports

CLAIM = (
    "every help a Vine program can print is named in the roster in "
    "docs/spec.md, every rule the roster names can be printed and is never "
    "printed as a note, and every section it points at exists"
)

SPEC = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "spec.md"
HEADING = "### The rules a report may offer"

# How many rules there are. Exact on purpose -- see the docstring.
EXPECTED = 12

# A roster line: the rule in backticks, then the section that states it, bold.
ENTRY = re.compile(r"^- `(.+)` — \*\*(.+)\*\*$")


def roster():
    """The (rule, section) pairs the roster lists, in the order it lists them."""
    pairs = []
    inside = False
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            inside = line.strip() == HEADING
            continue
        if inside:
            match = ENTRY.match(line.strip())
            if match:
                pairs.append((match.group(1), match.group(2)))
    return pairs


def headings():
    """Every section name in the document, at any level."""
    return {
        line.lstrip("#").strip()
        for line in SPEC.read_text(encoding="utf-8").splitlines()
        if line.startswith("#")
    }


def printed():
    """The help texts and the note texts the enumeration printed, each with a
    program that printed it."""
    helps, notes = {}, {}
    for source, error in reports():
        for label, text, _ in error.notes:
            (helps if label == "help" else notes).setdefault(text, source)
    return helps, notes


def check():
    listed = roster()
    rules = [rule for rule, _ in listed]
    offered, noted = printed()
    failures = []

    if len(listed) != EXPECTED:
        failures.append((
            HEADING,
            f"read {len(listed)} rules, not {EXPECTED} -- has the roster moved or changed shape?",
        ))
    for text, source in sorted(offered.items()):
        if text not in rules:
            failures.append((text, f"is offered by {source!r} and the roster does not name it"))
    for rule in rules:
        if rule not in offered:
            failures.append((rule, "is named in the roster and no program printed it"))

    for rule in rules:
        if rule in noted:
            failures.append((rule, f"is a rule and {noted[rule]!r} prints it as a note"))

    known = headings()
    for rule, section in listed:
        if section not in known:
            failures.append((rule, f"points at **{section}**, which is not a section"))

    return len(listed) + len(offered), failures
