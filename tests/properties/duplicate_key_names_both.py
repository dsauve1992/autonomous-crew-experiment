"""A duplicate map key is reported at two places: the caret on the second
appearance, and a note carrying the position of the first.

The sentence is `docs/spec.md`'s, in **Map order** -- *the caret is on the
second appearance and a note points at the first* -- and again in **Errors**,
where it is the reason three messages may quote a value without saying which
of two look-alike values they mean. Tick 23 chose not to reveal the duplicate
key on the strength of it. Nothing could check it. Deleting the `err.note(...)`
line from `eval_map` fails three goldens and no claim: a golden is a copy of a
message, so all three say is that the output changed, and the next tick reading
that diff has nothing to tell a regression from a tidy-up.
`spec_examples_run.py` cannot see it either -- it compares the *first line* of
a report, and a note is never on the first line.

Two halves, both about one set: the pairs of spellings that denote one key.

- A **duplicate** must produce both positions, and they must differ. The
  template puts the two keys on different lines *and* different columns, so a
  note that echoed the caret would be caught; before this file the three
  goldens all had the two keys on one line, which a line-only bug survives.
- A **distinct** pair must not be reported at all. Without this half the
  property passes for an implementation that calls every literal a duplicate,
  and the members are the ones that make the set worth having: two strings that
  print identically and are two keys, and `1`/`1.0`/`true`, which tick 3 made
  three keys rather than one.

Every column below is hand-written rather than computed from the spelling.
Computing them would need the rule that a parenthesised key reports the
expression inside the parens and not the paren, which is a thing the parser
decides -- and a property that derives its expectation from the code under test
has one side, not two.

`-0.0` and `0.0` are here because they are a look-alike pair with no Unicode in
them: `-0.0 == 0.0` is `true` in Vine, so they are one key, and the headline
says `0.0` while the note points at a line reading `-0.0`. The message is
unreadable without the position, and the reason has nothing to do with the
tables **Revealing** refuses.

Every clause was broken on its own, on a committed tree. Deleting the note
breaks ten; pointing the note at the caret's own position breaks the same ten;
putting the caret on the first appearance rather than the second breaks them
again. The second half has its own sabotages, listed beside DISTINCT.
"""

import io

from vine import run
from vine.errors import VineError

CLAIM = (
    "a map literal that gives one key twice names two places: the caret on the "
    "second appearance, and a note carrying the position of the first"
)

NAME = "<duplicate-key>"

# first spelling, its column, second spelling, its column. The template below
# fixes the lines: the first key is on line 3 and the second on line 4.
DUPLICATES = [
    ("a", 3, "a", 7),
    ("a", 3, '"a"', 7),
    ('"north"', 3, "north", 7),
    ("(region)", 4, "north", 7),
    ("north", 3, "(region)", 8),
    ("1", 3, "1", 7),
    ("1", 3, "(1)", 8),
    ("true", 3, "true", 7),
    ("-0.0", 3, "0.0", 7),
    ("0.0", 3, "-0.0", 7),
]

# Pairs that read as one key and are two. Each was sabotaged into a duplicate
# to check it guards something: `1`/`1.0` and `1`/`true` fall to dropping the
# type tag from `canonical`, the two strings to normalising with NFKC, and
# `"1"`/`1` to keying on `to_display`. `a`/`b` is the control -- two keys
# nothing sane collapses -- and is here to say so out loud.
DISTINCT = [
    ('"east 1"', '"east\\u{a0}1"'),
    ("1", "1.0"),
    ("1", "true"),
    ('"1"', "1"),
    ("a", "b"),
]


def program(first, second):
    return f'let region = "north"\nlet m = {{\n  {first}: 1,\n      {second}: 2,\n}}\n'


def report(src):
    """The rendered report, or None if the program ran."""
    try:
        run(src, NAME, io.StringIO())
    except VineError as e:
        return e.render()
    return None


def check():
    checked = 0
    failures = []

    for first, first_col, second, second_col in DUPLICATES:
        checked += 1
        src = program(first, second)
        shown = report(src)
        label = f"{{{first}: 1, {second}: 2}}"
        if shown is None:
            failures.append((label, "ran instead of reporting a duplicate key"))
            continue
        lines = shown.splitlines()
        if "gives the key" not in lines[0] or not lines[0].endswith("twice"):
            failures.append((label, f"headline was {lines[0]!r}"))
            continue
        want_caret = f" --> {NAME}:4:{second_col}"
        if lines[1] != want_caret:
            failures.append((label, f"caret line was {lines[1]!r}, not {want_caret!r}"))
            continue
        notes = [ln for ln in lines if ln.lstrip().startswith("= note:")]
        if len(notes) != 1:
            failures.append((label, f"{len(notes)} notes, not 1: {notes}"))
            continue
        # Two spaces: a note is indented under the gutter, which is one
        # character wide here because the caret is on line 4.
        want_note = f"  = note: the key is first given at 3:{first_col}"
        if notes[0] != want_note:
            failures.append((label, f"note was {notes[0]!r}, not {want_note!r}"))

    for first, second in DISTINCT:
        checked += 1
        shown = report(program(first, second))
        if shown is not None:
            failures.append((
                f"{{{first}: 1, {second}: 2}}",
                "reported as a duplicate: " + shown.splitlines()[0],
            ))

    return checked, failures
