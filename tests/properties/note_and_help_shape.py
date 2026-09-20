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

Six clauses, each broken on its own, on a committed tree.

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
4. **No extra line repeats the one above it.** Clause 2 is this one for a
   report that carries a single note, and it was written when that was every
   report there was. Tick 29's call chain made a report that carries several,
   and the first draft of it printed `pong was called at 1:24` three times --
   each true, each a different call, and the whole suite green. A position
   the line above already gave is not a second place to look either.
5. **A help quotes no position.** The structural half of *a help carries no
   position* cannot fail and is not asserted: `help()` has no parameter for
   one. What can fail is the text, so what is checked is the text -- a help
   whose words quote a `line:col` is a fact about this program wearing a
   rule's label.
6. **No note comes after a help.** Facts about this program, then rules of
   the language: **Errors** says so and every report has read that way. It
   held by arithmetic until tick 36 -- one note added before one help -- and
   the call-depth report is the first whose help is attached before its notes
   exist. `note_lines()` orders by what a line is rather than by when it was
   written, and this is what says it still does. Order by insertion there and
   one program fails here on three lines -- the mutual recursion, which is the
   only one in the enumeration whose help arrives before its notes.

**What the grid reaches, and what it does not.** `no_traceback.py` enumerates
75,167 programs by varying *types* -- every builtin against every value, every
operator between every pair, every pair and triple of source fragments. That
reaches 29 of the 46 `.note(`/`.help(` sites in `vine/`. The seventeen it
misses all need a specific mistake rather than a wrong type: a codepoint
escape that is malformed in one of four ways, a map literal that repeats a
key, a hole with a format after it, `"{{`, a string Python reads as a number
and Vine does not, a keyword written where the grid only ever writes values,
a call that fails inside a function the program itself wrote, a key with
a function nested inside it rather than being one, a value built deeper
than anything will walk -- which the grid cannot reach because every value in
it is written out, and this one takes a loop to build -- and a call nested
five hundred deep, which the grid never nests a call at all to reach.
`MISTAKES` below is those, hand-written, one line of why each, and with them
the enumeration reaches all 46. The mutual recursion among them reached no
site of its own until tick 36 gave the call limit a help: it was there for a
*shape* rather than a site, because clause 4 is about two lines and every
other program here prints at most one that could repeat, and it is still the
only program here that checks that clause.

The pair of numbers above was `28` and `seventeen` from tick 26 until tick 36,
which adds to 45 and was wrong at the first: the grid reached 29 even then.
Only their sum was ever checked, by `EXPECTED_SITES` and by nothing else.
Measured, this tick, by recording the line each `.note(` and `.help(` call
came from while the grid and `MISTAKES` ran -- the dynamic set and the static
one this file greps for are the same 46 lines.

Tick 43 added four sites with `import`: three helps in the parser and the
interpreter for a name that is not a string, a name with a hole in it and a
file that is not there, and one for a cycle. All four need the keyword, which
the grid never writes, so all four are in `MISTAKES`.

**What nothing here reaches.** A note pointing into a *different source* than
the caret renders `name:line:col` rather than `line:col`. Until tick 43 only
the REPL had two sources alive at once and `tests/cases/repl/notes.repl` was
the one case that printed that form, compared only with itself. An import has
two as well -- the caret is in the imported file and `imported at {pos}` names
the line that reached for it -- so `import "loop.vine"` now checks the clauses
above on a cross-source note, on the error object. The REPL's own remains a
golden, because the REPL catches its errors and does not hand them back.
"""

import io
import pathlib
import re

import no_traceback
from vine import run
from vine.errors import VineError

CLAIM = (
    "every extra line under a caret is a note or a help; a note's position is "
    "never the caret's; no extra line repeats the one above it; a {pos} in "
    "the text and a position come together; no help quotes a position; no "
    "note comes after a help; and vine/ holds the number of sites this file "
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
EXPECTED_SITES = 54  # the 47th is read()'s, reached by the grid's zero-argument call
# Where the programs run, so that an `import` in one resolves somewhere fixed.
# A generated program has no file, and without this its imports would be
# looked for beside whoever ran ./check. The path names no real file: what is
# used of it is its directory, which is where `tests/fixtures/loop.vine` is.
FIXTURES = (
    pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "<report>.vine"
)
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
    "fail",                # the one statement with no bare form, written bare
    'fail "  "',           # and the same rule where only a value can carry it:
                           # a message the grammar saw and the terminal cannot
    # A failure four calls down: the frame notes that say which call reached
    # it, and the line counting the ones the report has no room for. The grid
    # varies types and never nests a call, so nothing in it has a caller.
    "let a = fn() { 1 / 0 }\n"
    "let b = fn() { a() }\n"
    "let c = fn() { b() }\n"
    "let d = fn() { c() }\n"
    "d()",
    # Mutual recursion, which is the one shape that can make a report repeat
    # a line: the caret is on one of the two calls, so every frame at that
    # position is dropped and the other is reached five hundred times. Take
    # the guard out of `frame()` and clause 4 fails here -- without this
    # program it passes, and the guard is one nothing has watched fire.
    "let ping = fn(n) { pong(n) }\nlet pong = fn(n) { ping(n) }\nping(0)",
    # A key with a function *inside* it. The grid offers every value to every
    # builtin, so it reaches a key that IS a function; a key that merely holds
    # one is a list whose element is a function, which is a value the grid
    # never builds. The note it reaches is the one that says where.
    "set({}, [print], 1)",
    # A value deeper than any walk will go. Built by a loop rather than
    # written, because the parser stops a literal at 200 -- so no program
    # the grid can write reaches this site at all.
    "print(reduce(range(1001), fn(a, i) { [a] }, []))",
    # The four import sites. The grid varies types and every one of these
    # needs the keyword, which it never writes.
    'import "no_such_table.vine"',   # a neighbour that is not there
    "import 1",                      # a name that is not a string at all
    'import "{1}.vine"',             # a name with a hole in it
    # A file that imports itself, which is also the only program here whose
    # note points into a different source than its caret -- see the last
    # paragraph of the docstring above.
    'import "loop.vine"',
]


def reports():
    """Every failing program checked here, as (source, the error it raised).

    Shared with `help_roster.py`, which asks a different question of the same
    reports. A copied enumeration is the half that stops growing when the
    original does not.
    """
    for source in list(no_traceback.programs()) + MISTAKES:
        try:
            run(source, "<report>", io.StringIO(), origin=FIXTURES)
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
        previous = None
        helped = False
        for line in rendered.splitlines():
            stripped = line.lstrip()
            if not stripped.startswith("= "):
                continue
            if stripped == previous:
                failures.append((source, f"repeats the line above it: {stripped}"))
            previous = stripped
            label = stripped[2:].split(":", 1)[0]
            if label not in ("note", "help"):
                failures.append((source, f"extra line labelled {label!r}: {stripped}"))
            if label == "help" and POSITION.search(stripped):
                failures.append((source, f"a help quotes a position: {stripped}"))
            if label == "help":
                helped = True
            elif helped:
                failures.append((source, f"a note comes after a help: {stripped}"))
        for label, text, pos in error.notes:
            if "{pos}" in text and pos is None:
                failures.append((source, f"{label} says {{pos}} and has none: {text}"))
            if pos is not None and "{pos}" not in text:
                failures.append((source, f"{label} carries a position it never writes: {text}"))
            if pos is not None and same_place(pos, error):
                failures.append((source, f"{label} repeats the caret's position: {text}"))
    return checked, failures
