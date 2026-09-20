"""The keyword list in **Lexical structure** is the set the lexer reserves,
and every word on it really is refused where a name is wanted.

Tick 26 made `return` a keyword. `./check` stayed green: 152 cases and
properties, and not one of them could tell that the document's list of
keywords had just become wrong. That list is the only place a reader is told
which words they may not use as names, and it was held by nobody.

Three clauses, and the third is why this is not two copies of one list.

1. **Every word the lexer reserves is listed.** A keyword added and not
   written down is the direction `roster_names_every_builtin.py` was written
   for, and it fails the same way: silently, for as long as nobody happens to
   type the word.
2. **Every word listed is reserved.** A keyword removed with the document left
   behind reads as a rule that costs the reader a name for nothing.
3. **Every word listed is actually refused as a name, and the message names
   it.** This is the half a pair of lists cannot check. Reserving a word in
   the lexer and refusing it in the parser are two things, and the parser
   refuses names at three sites -- after `let`, in a parameter list, and after
   `.` -- which is three chances for one of them to have been written to
   accept a keyword. The check runs all three for every keyword and reads the
   message, because `expected a name` with no name in it is a refusal a reader
   cannot act on.

   The bare map key is *not* among them, deliberately: `map_key` falls back to
   an expression, so `{true: 1}` is a map keyed by the boolean and `{return: 1}`
   is a syntax error. That is a difference between keywords rather than a
   property of them, and the escape hatch is the same for both -- `{"W": 1}`
   is a key of that spelling whatever W is, which is the fourth program run
   here and the one that has to keep working.

Against an over-eager match there are the near misses: words that *contain* a
keyword and must still be names. `lets`, `returns` and `android` are names in
any language that reserves `let`, `return` and `and`, and a lexer that matched
a prefix rather than a whole word would take all three.
"""

import io
import pathlib
import re

from vine import run
from vine.errors import VineError
from vine.lexer import KEYWORDS

CLAIM = (
    "the keyword list in docs/spec.md is the set the lexer reserves, every "
    "word on it is refused where a name is wanted and named in the refusal, "
    "and a word that merely contains one is still a name"
)

SPEC = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "spec.md"
# The roster line: `- Keywords: ` and then the whole set in one backtick span.
LINE = re.compile(r"^- Keywords: `([a-z ]+)`\.$")

# How many there are. Exact, for the reason help_roster.py gives: a property
# that reads a document has one clause more than it looks, and it is how much
# it read.
EXPECTED = 14

# The three places the parser wants a name. `{}` is bound first so the third
# has something to reach into; what is being checked is the parse, and the
# parse fails before any of it runs.
AS_A_NAME = [
    "let {word} = 1",
    "let f = fn({word}) {{ 1 }}",
    "let o = {{}}\no.{word}",
]

# Words that contain a keyword and are not one.
NEAR_MISSES = [
    "lets", "returns", "iffy", "android", "orbit", "note",
    "doing", "elsewhere", "nilpotent", "fnord", "truest", "falsehood",
]


def fails(source):
    """The first line of the report `source` raises, or None if it ran."""
    try:
        run(source, "<keywords>", io.StringIO())
    except VineError as error:
        return error.render().splitlines()[0]
    return None


def listed():
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        match = LINE.match(line.strip())
        if match:
            return match.group(1).split()
    return []


def check():
    words = listed()
    failures = []
    checked = len(words) + len(KEYWORDS)

    if len(words) != EXPECTED:
        failures.append((
            "- Keywords:",
            f"read {len(words)} keywords, not {EXPECTED} -- has the line moved "
            "or changed shape?",
        ))
    for word in sorted(KEYWORDS):
        if word not in words:
            failures.append((word, "is reserved by the lexer and the Keywords line does not name it"))
    for word in words:
        if word not in KEYWORDS:
            failures.append((word, "is on the Keywords line and the lexer does not reserve it"))

    for word in words:
        for template in AS_A_NAME:
            source = template.format(word=word)
            checked += 1
            first = fails(source)
            if first is None:
                failures.append((source, "is a keyword used as a name and Vine accepted it"))
            elif f"keyword {word!r}" not in first:
                failures.append((source, f"is refused as {first!r}, which does not name the keyword"))
        source = f'{{"{word}": 1}}'
        checked += 1
        if fails(source) is not None:
            failures.append((source, "is the string spelling of a keyword key and Vine refused it"))

    for word in NEAR_MISSES:
        source = f"let {word} = 1\n{word}"
        checked += 1
        if fails(source) is not None:
            failures.append((source, "is not a keyword and Vine refused it as a name"))

    return checked, failures
