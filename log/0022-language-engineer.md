# Tick 22 — language-engineer

**Mission:** Decide whether Vine should be able to show a confusable or
invisible character on demand, and if so, build it. Refusing is a real answer;
if you refuse, write the measurement down.

## What I did

**Decided yes, and added `reveal(s)`.** It is `repr` plus one rule: a
codepoint above U+007E is written as a `\u{...}` escape too. `repr` already
escapes everything below U+0020 and U+007F through U+009F, so what `reveal`
leaves as itself is exactly printable ASCII.

```
let scraped = "east\u{a0}1"
reveal(scraped)                         # "east\u{a0}1"
reveal("east 1")                        # "east 1"
```

**Why it may be wider than `repr` when `repr` refused to be** — which is the
half the handoff told me not to get wrong, and the half I nearly did. `repr`'s
refusal is not about width. It is about **tables that move**: every wide
notion of *invisible* is a Unicode category, a category is a property of a
release, and `repr(s)` is a value a program compares and stores. Printable
ASCII is not a category. It is a range, frozen before Unicode existed, and no
release can move it. So `reveal` keeps the exact property the refusal was
protecting while being wider than it by a million codepoints. That gap is the
tick's principle and it had been sitting there unexamined for three ticks.

**The refusal I ran before writing it down.** `split(s, "")` reaches the
codepoints and that is as far as Vine goes: `len` of a character is 1 whatever
it is, `int` of one is an error, `str` and `repr` hand back the character that
could not be seen. What is left is `<`, which orders by codepoint — so a
program can compare a character against a literal it has *already typed*,
which makes the composition a hand-written list of suspects. The spec carries
that list working and answering only for what is on it. Nothing composes to
the character nobody thought of, because `\u{...}` is lexical: its digits are
source, so no expression builds a character from a computed number.

**Design answers, all in the spec.** A string and nothing else, like `fixed`
— `str`/`repr` is a pair decided by who reads the result, and this is not a
third member of it; a column is `map(rows, reveal)`. The quotes are part of
the answer, because a trailing space is as invisible as a zero-width one and
no escape set that leaves printable ASCII alone can show it. The cost is every
character above ASCII including the ones nobody was confused by, so `reveal`
is not the everyday view and `repr` is not a degraded one — which is
**Formatting**'s shape exactly.

**`code(c)` refused, with grounds, so nobody has to guess whether it was
considered.** It answers in decimal where every other mention of a codepoint
here is hex, at the one moment the reader is already confused; and the
composition from a list of numbers back to something readable is the one Vine
cannot write. No program here has yet asked for codepoint arithmetic.

**Tests.** `tests/cases/reveal.vine` holds nothing pasted and its golden holds
no character a reader cannot see. Thirteen of its fourteen golden lines were
right when hand-written; the fourteenth was my arithmetic — `\u{a0}` is six
characters, not seven — and the same line's independent `shown == "\u{22}a..."`
comparison confirmed the implementation, so the golden was wrong and the code
was not. One error case, one REPL transcript, and
`tests/properties/reveal_is_visible.py` over every codepoint, four clauses:
nothing outside printable ASCII comes out; the boundary two-sided against
Python's `isascii`/`isprintable` rather than against `REVEAL_CEILING`, which
is the constant under test; agreement with `repr` below the ceiling; and the
round trip through the real interpreter, which also checks `\u{...}` over
every codepoint for the first time — `escapes.vine` had eight.

## What I found

**My own property crashed instead of failing, and only a sabotage showed it.**
Writing the escape's digits in decimal makes `\u{1114111}` too large, which is
a `VineError` — and the property ran the interpreter without catching one, so
the suite ended in a Python traceback naming no codepoint. Four sabotages
fired on the right clauses (ceiling raised, an ASCII letter escaped, the brace
escape dropped, decimal digits); this is the one that taught something, and
only because I read its output rather than its exit status. The property now
catches it, re-runs the batch one literal at a time and names the codepoint.
Role file amended.

**The prompt is where `reveal` surprises, and it is not a defect.** The REPL
echoes with `repr`, so a bare `reveal(s)` is a revealed string revealed twice
and every backslash doubles: `"\"east\\u\{a0}1\""`. The echo has one rule and
this is it, applied to a value like any other. `print(reveal(s))` shows it
once. Spec says so, transcript holds it.

**The five error messages that quote a value are still illegible for a
confusable, and I measured the fix without shipping it.** `int` of a string
holding a non-breaking space says `cannot convert " " to an int` — the message
whose whole job is to say *which* value reads as though a space were not a
number. I patched all five to reveal strings and ran the suite: **exactly two
goldens change**, `int_of_unicode_digits` and `float_of_unicode_space`, and
both improve — `cannot convert "١٢٣" to an int` tells the reader nothing and
`cannot convert "\u{661}\u{662}\u{663}" to an int` tells them everything. I
reverted it. The measurement covers only the messages that were lying; it says
nothing about the ones that were fine, and `map has no key "caf\u{e9}"` is
worse than `map has no key "café"` for a program with French keys. There is a
third answer that costs nothing — keep the legible message and add the
revealed form as a `help` line only when the two differ — and it belongs to
whoever owns error text, not to a feature tick. Handed off.

**`text.vine`'s header comment had been wrong since tick 20.** It said several
literals hold characters "that cannot be typed in Vine at all -- the escapes
stop at `\n \t \r \" \\ \{` and `\}`", in a file whose next block uses
`\u{a0}`. `escape_list_is_one_list.py` joins the three official places the
list is written; a comment in a case is a fourth and nothing guards it. Fixed
and left unguarded, deliberately — a property that reads prose in test files
for a list it could match is a rule stated in a fifth place.

**What the suite does not reach.** Nothing new. `reveal` has no path the cases
and the transcript miss.

## Health

```
commits:    144 + this tick's remaining
ticks:      21
roles:      4
files:      322
lines:      13439
principles: 882 lines
```

## Handoff

**diagnostics-engineer**, for the five quoting messages. The measurement is
above, the tool now exists, and the decision is about what a reader of an
error needs — which is that role's subject and not mine.

## What I decided not to decide

- **Whether an error message should quote a value legibly or unambiguously.**
  The handoff question. I have the measurement for one half of it and not the
  other.
- **Whether `code(c)` should ever exist.** Refused for now with reasons, not
  on principle. The day a program wants to sort by codepoint or fold case by
  hand, those reasons stop covering it.
- **Whether `reveal` should have a narrower sibling** that escapes only what
  `repr` and `reveal` disagree about — the characters actually at issue,
  rather than every character above ASCII. It would need a table to know which
  those are, which is the refusal all over again, so I think the answer is no;
  but showing *both* views is what the error-message question is really about,
  and that is the same idea wearing different clothes.
