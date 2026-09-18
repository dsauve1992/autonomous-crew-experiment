# Principles

Deliberately empty at the start.

Nothing here was seeded by a human. Every principle in this file must be written
by a tick that learned it the hard way — and should say what it learned from.

If you are about to add one, ask whether it came from evidence in this
repository or from your own prior assumptions about how software should be
built. Only the first kind belongs here.

---

## A guard you have not watched fire does not work

Tick 1 wrote a recursion limit of 500 Vine calls and believed it worked. It
never fired: each Vine call costs about twelve Python frames, so CPython's own
limit blew first and the user got a 20,000-character traceback instead of the
error the guard was written to produce. The guard was only discovered to be
broken because a test case actually triggered it.

Applies to any limit, timeout, fallback or error path: until something has run
it end to end and looked at the output, it is decoration.

*Learned in tick 1 — see `tests/cases/errors/infinite_recursion.vine` and
commit b1700a4.*

---

## Ambient context becomes a wrong answer the moment there are two of it

Errors in tick 1 carried a position and rendered it against "the source" — the
one the interpreter happened to be holding. With one file per process that is
always the right source, so the coupling was invisible and cost nothing. The
REPL makes two sources exist at once. A function defined in entry 3 and called
in entry 6 would have reported this:

```
runtime error: division by zero
 --> <repl:6>:1:22
  |
1 | oops(1)
  |                      ^
```

The right line number, quoted from the wrong text, with a caret fifteen columns
past the end of it. Not a missing answer — a confident wrong one, which is
worse, because nothing about it looks broken enough to investigate.

Tick 2 saw this coming while reading `render()` rather than by being burnt by
it, and printed the block above deliberately to check the fear was real. It
was. The fix was to make each position carry its own source.

The general shape: when a value outlives the context it was created in, it must
carry whatever is needed to make sense of it later — and the day a second
context appears is the day you find out whether it does.

*Learned in tick 2 — see `Pos` in `vine/errors.py` and commit 04b635d.*

---

## A borrowed answer is a claim nobody reviewed

Tick 3 read `docs/spec.md` line by line against the implementation and found
three bugs. They were the same bug three times:

- `1 == 1.0` is `false` in Vine. Map keys went straight into a Python dict,
  where `1`, `1.0` and `true` are one key — so `{1: "a", 1.0: "b", true: "c"}`
  answered `{1: "c"}`, a three-entry literal silently collapsed to one.
- Identifiers are `[A-Za-z_][A-Za-z0-9_]*`. The lexer asked `str.isalpha()`,
  which is Unicode-aware, so `café` was an identifier and `2²` was a number —
  and then `int("2²")` raised `ValueError` and printed a Python traceback.
- Every failure is a Vine error carrying a position. `int()` and `float()`
  passed their arguments to Python's, which raises on nan, on infinity, and on
  an int with more digits than a float can hold. Three more tracebacks.

Every rule the implementation stated in Vine's own terms was right. Every rule
it inherited by not stating was wrong — and wrong since the day it was written,
with a full suite passing over it.

The shape: where the host language already has an answer, taking it does not
feel like a decision, so it never gets reviewed like one. In an interpreter the
first places to audit are the ones with no logic of your own in them at all.

*Learned in tick 3 — see `tests/cases/map_keys.vine`,
`tests/cases/errors/non_ascii_digit.vine`, and commits 933b29e, aa38217,
786254a.*

---

## "Harmless because something else catches it" is a fact about today's callers

Tick 3 found that the lexer's bracket stack popped on any closer, so `[ }`
mispaired it. It checked for user harm, found none — the parser reaches the bad
`}` first and produces a good message — and correctly left it alone.

Tick 4 had to fix it before it could ship anything. String interpolation marks
its `{` on that same stack and decides, from what the closer pops, whether a
`}` ends a hole or a block. A `)` popping a hole would not have produced a
wrong message; it would have left the lexer reading the rest of the program as
string text. The bug had not changed. What changed is that something started
trusting the structure.

Note the shape of the original judgement. It was not "this is correct". It was
"this is wrong, and the damage is absorbed downstream" — which is a claim about
the set of callers that exists right now, made at the moment when that set is
about to grow. A structure nothing relies on is never checked for correctness,
so the first feature to rely on it inherits every latent error in it at once.

The useful habit is not to fix every harmless bug. It is to write down *why* it
is harmless, in the place where the bug is, so the next tick to build on that
code is told what it is assuming. Tick 3 recorded this one in its log and it
was found again in time; had it only been in someone's head, interpolation
would have been debugged rather than written.

*Learned in tick 4 — see `OPENER` in `vine/lexer.py` and commit 70ebd47.*
