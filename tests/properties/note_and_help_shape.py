"""Every extra line under a caret has the shape **Errors** promises.

`docs/spec.md` states the note/help contract in three sentences: *a note
states a fact about this program and carries a position where there is one; a
help offers a rule of the language and carries none; the caret is where the
failure was detected and a note may name where it was caused.* Until tick 25
nothing in the suite could break any of them. Every message that carries a
note or a help was guarded by a golden, and a golden is a copy of the message
it checks -- it fails when the text changes and says nothing about whether the
text was ever right. `spec_examples_run.py` is the one property that reads the
document, and it compares the **first line** of a report; a note is never on
the first line.

Four clauses, each broken on its own, on a committed tree.

1. **Every extra line is labelled `note` or `help`, and nothing else.** This
   is the one the reader parses by eye, and it is the whole of what tells a
   fact about their program from a rule of the language. Changing `"help"` to
   `"hint"` in `errors.py` fails 3898 programs here.
2. **A note's position is never the caret's.** A note that names the place
   the caret already points at costs a line and adds nothing. Written for
   `duplicate_key_names_both.py`'s one message and taken to all of them, this
   clause found the defect the same tick fixed: at end of input the parser
   moves the caret onto the innermost unclosed bracket, and `waiting()`'s note
   then said `the '(' at 1:1 is still open` under a caret already on that `(`.
   308 programs; one golden, and it was the case where the note is right.
3. **A `{pos}` in the text and a position come together.** A template with a
   `{pos}` and no position renders the braces to the user; a position with no
   `{pos}` in the text is a second place to look that is silently dropped.
   Both directions fire -- dropping the `at` argument at `lexer.py`'s codepoint
   note breaks the first, deleting ` at {pos}` from the text breaks the second.
4. **A help quotes no position.** The structural half of *a help carries no
   position* cannot fail and is not asserted: `help()` has no parameter for
   one. What can fail is the text, so what is checked is the text -- a help
   whose words quote a `line:col` is a fact about this program wearing a
   rule's label.

**What the grid reaches, and what it does not.** `no_traceback.py` enumerates
75,167 programs by varying *types* -- every builtin against every value, every
operator between every pair, every pair and triple of source fragments. That
reaches 26 of the 39 `.note(`/`.help(` sites in `vine/`. The thirteen it
misses all need a specific mistake rather than a wrong type: a codepoint
escape that is malformed in one of four ways, a map literal that repeats a
key, a hole with a format after it, `"{{`, a string Python reads as a number
and Vine does not, and a keyword written where the grid only ever writes
values. `MISTAKES` below is those, hand-written, one line of why each, and
with them the enumeration reaches all 39.

**What nothing here reaches.** A note pointing into a *different source* than
the caret renders `name:line:col` rather than `line:col`, and only the REPL
has two sources alive at once. `tests/cases/repl/notes.repl` is the one case
that prints that form, and it is a golden -- so the rendering of a cross-source
note is still compared only with itself. The clauses above are checked on the
error object, which the REPL catches and does not hand back.
"""

import io
import pathlib
import re

import no_traceback
from vine import run
from vine.errors import VineError

CLAIM = (
    "every extra line under a caret is a note or a help; a note's position is "
    "never the caret's; a {pos} in the text and a position come together; no "
    "help quotes a position; and vine/ holds the number of sites this file "
    "claims to reach"
)

# A position as note_lines() writes one: `3:7`, or `<repl:1>:3:7`.
POSITION = re.compile(r"\d+:\d+")

# Where the sites are, and how many the paragraph above claims to reach. The
# count is checked because the claim is *all* of them: a 38th site added with
# this file left alone would leave a docstring saying the enumeration is
# exhaustive when it no longer is, and nothing else in the suite reads either
# number. Tick 26 wrote this after walking its own change against the suite
# and finding the count of the moment -- 36 -- held by nobody. If you add a
# site, add the program that reaches it and move this number in the same
# commit; if the program is genuinely impossible, say so beside the number.
SITES = re.compile(r"\.note\(|\.help\(")
EXPECTED_SITES = 39
VINE = pathlib.Path(__file__).resolve().parent.parent.parent / "vine"

# Programs reaching a note or a help the type grid cannot, and why it cannot.
MISTAKES = [
    'float("1e400")',      # the shape of a number, past every float there is
    'float("inf")',        # Python reads it; Vine has no infinities
    'float("\u0661")',   # digits that are digits only in Unicode
    "let m = {a: 1,\n  a: 2}",  # one key twice, on two lines and two columns
    '"\\uZ"',              # a codepoint escape with no brace
    '"\\u{1g}"',           # a codepoint escape the hex runs out of
    '"\\u{}"',             # a codepoint escape with no digits
    '"\\u{d800}"',         # a codepoint that is not a character
    '"\\u{110000}"',       # past the last codepoint: the one escape message here
                           # that offers no rule, because its headline already
                           # names the limit. It is enumerated so that
                           # help_roster.py can see a rule added to it.
    '"{1:2}"',             # a hole with a format after it
    '"{{1}}"',             # the doubled brace every other language accepts
    "take([1], -1)",       # a count that is not a quantity
    "fixed(1, 2000)",      # more decimal places than any float has
    "return 1",            # a statement of a function body, outside one
]


def reports():
    """Every failing program checked here, as (source, the error it raised).

    Shared with `help_roster.py`, which asks a different question of the same
    reports. A copied enumeration is the half that stops growing when the
    original does not.
    """
    for source in list(no_traceback.programs()) + MISTAKES:
        try:
            run(source, "<report>", io.StringIO())
        except VineError as error:
            yield source, error
        except Exception:
            pass  # no_traceback.py is what says this may not happen


def same_place(pos, error):
    """Whether `pos` names the character the caret is on.

    A note's position may carry its own source; when it does not, it is read
    against the one the report quotes -- which is what `render()` does, and
    why this cannot just compare line and column.
    """
    caret = error.pos
    if caret is None:
        return False
    fallback = caret.source or error.source
    return (pos.source or fallback) is (caret.source or fallback) and (
        pos.line,
        pos.col,
    ) == (caret.line, caret.col)


def sites():
    """How many `.note(`/`.help(` calls `vine/` holds."""
    return sum(
        len(SITES.findall(path.read_text(encoding="utf-8")))
        for path in sorted(VINE.glob("*.py"))
    )


def check():
    checked = 0
    failures = []
    found = sites()
    checked += 1
    if found != EXPECTED_SITES:
        failures.append((
            "vine/*.py",
            f"holds {found} note and help sites, not {EXPECTED_SITES} -- the "
            "docstring here claims the enumeration reaches every one, so a "
            "site added needs a program that reaches it",
        ))
    for source, error in reports():
        if not error.notes:
            continue
        checked += 1
        rendered = error.render()
        for line in rendered.splitlines():
            stripped = line.lstrip()
            if not stripped.startswith("= "):
                continue
            label = stripped[2:].split(":", 1)[0]
            if label not in ("note", "help"):
                failures.append((source, f"extra line labelled {label!r}: {stripped}"))
            if label == "help" and POSITION.search(stripped):
                failures.append((source, f"a help quotes a position: {stripped}"))
        for label, text, pos in error.notes:
            if "{pos}" in text and pos is None:
                failures.append((source, f"{label} says {{pos}} and has none: {text}"))
            if pos is not None and "{pos}" not in text:
                failures.append((source, f"{label} carries a position it never writes: {text}"))
            if pos is not None and same_place(pos, error):
                failures.append((source, f"{label} repeats the caret's position: {text}"))
    return checked, failures
