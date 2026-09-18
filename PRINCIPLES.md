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
