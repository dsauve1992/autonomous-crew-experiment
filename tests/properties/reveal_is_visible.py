"""Every character of `reveal` output can be seen, and the output is source.

The promise `repr` deliberately does not make. **repr and str** says `repr` is
legible and not unambiguous: a non-breaking space reprs as itself and reads as
a space, a zero-width space reprs as itself and reads as nothing at all. The
refusal is right -- the wide notions of *invisible* are Unicode categories,
which move between releases, and `repr(s)` is a value a program stores and
compares. **Revealing** fills the hole beside it instead: `reveal(s)` escapes
every codepoint above U+007E, and printable ASCII is frozen.

So this file is the sentence `repr_is_legible.py` is not allowed to say. That
one's INVISIBLE set carries a warning not to widen it, because widening it
would assert a promise `repr` does not make. This is where the wider promise
lives, about the function that does make it.

Four clauses, and the last one is the expensive one:

- Nothing outside U+0020 to U+007E comes out. That is the promise.
- The boundary, two-sided, against Python's own `isascii`/`isprintable`
  rather than against `REVEAL_CEILING`, which is the constant under test. The
  two agree because ASCII was frozen before Unicode existed, which is the
  whole argument for the ceiling being where it is.
- Below the ceiling, `reveal` and `repr` are the same function. `reveal` is
  specified as *`repr` plus one rule*, so a change to either that makes them
  disagree down there is a change to that specification, and should have to
  say so here.
- The round trip, over every codepoint, through the real interpreter. This
  also checks something nothing else does: that `\\u{...}` lexes back to the
  codepoint it names, for every codepoint rather than the eight in
  `tests/cases/escapes.vine`. Batched a few thousand literals to a program,
  because a run each is a couple of minutes and a list literal is flat.

Surrogates are not here. A Vine string cannot hold one -- the lexer refuses
the escape and `repr_is_legible.py` watches it refuse -- so `reveal` can never
be handed one, and checking it here would be checking the lexer twice.
"""

import io

from vine import run
from vine.errors import VineError
from vine.values import REVEAL_CEILING, to_repr, to_reveal

CLAIM = (
    "reveal writes every codepoint above printable ASCII as an escape and "
    "nothing else, agrees with repr below that, and its output is Vine "
    "source that reads back as the string it was given"
)

# The codepoints `reveal` output is allowed to hold, written from Python's
# notion of ASCII rather than from `REVEAL_CEILING`. `str.isprintable` counts
# the space and nothing else below U+0021, which is what a reader of a quoted
# string wants: the quotes are what show a space at either end.
VISIBLE = frozenset(
    c for c in range(0x80) if chr(c).isascii() and chr(c).isprintable()
)

# The three characters in VISIBLE that `reveal` still writes as an escape,
# for the reasons `repr` does: a quote would end the string, a backslash
# would begin another escape, a brace would open a hole.
STRUCTURAL = frozenset(ord(ch) for ch in '"\\{')

SURROGATES = range(0xD800, 0xE000)

CHUNK = 4000


def check():
    """Returns (how many codepoints were checked, the ones that broke it)."""
    failures = []
    checked = 0
    codepoints = [c for c in range(0x110000) if c not in SURROGATES]

    for c in codepoints:
        checked += 1
        char = chr(c)
        text = to_reveal(char)

        unseen = sorted(set(ord(ch) for ch in text) - VISIBLE)
        if unseen:
            shown = " ".join(f"U+{u:04X}" for u in unseen)
            failures.append((f"U+{c:04X}", f"reveal is {text!r}, which holds {shown}"))

        # The boundary, from the other side. A codepoint stays as itself
        # exactly when it is printable ASCII and is not one of the three the
        # syntax needs escaped.
        stays = text == f'"{char}"'
        should_stay = c in VISIBLE and c not in STRUCTURAL
        if stays != should_stay:
            if should_stay:
                why = "it is printable ASCII and the syntax does not need it escaped"
            elif c in STRUCTURAL:
                why = "the syntax needs it escaped, printable ASCII or not"
            else:
                why = "it is not printable ASCII, so it may not be left alone"
            failures.append((f"U+{c:04X}", f"reveal is {text!r}: {why}"))

        # reveal is repr plus one rule, and this is everything below the rule.
        if c <= REVEAL_CEILING and text != to_repr(char):
            failures.append(
                (
                    f"U+{c:04X}",
                    f"reveal is {text!r} where repr is {to_repr(char)!r}, "
                    "and below the ceiling they are one function",
                )
            )

    for start in range(0, len(codepoints), CHUNK):
        chunk = codepoints[start : start + CHUNK]
        try:
            back = evaluate(chunk)
        except VineError:
            # Output that does not parse at all fails the whole chunk, so the
            # chunk is re-run one literal at a time to say which codepoint.
            # Found by sabotage: writing the escape's digits in decimal makes
            # `\u{1114111}` too large, and before this the VineError left the
            # property as a Python traceback rather than as a failure.
            failures.extend(one_at_a_time(chunk))
            continue
        for c, value in zip(chunk, back):
            if value != chr(c):
                failures.append(
                    (f"U+{c:04X}", f"reveal is {to_reveal(chr(c))!r}, which read back as {value!r}")
                )

    return checked, failures


def evaluate(codepoints):
    """The reveal of each codepoint, run as one Vine list literal."""
    source = "[" + ", ".join(to_reveal(chr(c)) for c in codepoints) + "]"
    return run(source, "<property>", io.StringIO())


def one_at_a_time(codepoints):
    failures = []
    for c in codepoints:
        text = to_reveal(chr(c))
        try:
            back = evaluate([c])
        except VineError as exc:
            failures.append((f"U+{c:04X}", f"reveal is {text!r}, which is not source: {exc.message}"))
            continue
        if back[0] != chr(c):
            failures.append((f"U+{c:04X}", f"reveal is {text!r}, which read back as {back[0]!r}"))
    return failures
