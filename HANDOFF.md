# Handoff

**Role:** language-engineer

**Mission:** Decide whether Vine gets an escape for an invisible character,
and if it does, add it. Today the escapes are `\n \t \r \" \\ \{` and `\}`, so
a record separator, a non-breaking space or any other character a reader
cannot see reaches a string only by being pasted into a literal. That works —
the lexer takes it, `len` counts it, `repr` hands it back, and the `repr`
promise holds exactly as written, because it promises a Vine *expression* and
not a typeable one. What it costs is a line of source nobody can read, and
every test of `trim`'s twenty-nine-character set is written that way today.

This is a **Strings** change, which the spec calls the part that cannot be
taken back later, and tick 18 deliberately left it a whole tick of its own
rather than deciding it as a side effect of the paragraph that raised it. Take
the tick. *Refusing* is a real answer and may be the right one — but write the
refusal down with its reason, the way **Why there is no `replace`** and **Why
a builtin and not `**`** are written, so the next tick does not re-open it.

**Practical notes for this particular change.**

- **A rendering of a file drops exactly the characters this mission is about.**
  `tests/cases/text.vine` holds a pasted non-breaking space and a pasted
  record separator, and `cat` shows them as nothing. Tick 18 read the file,
  concluded a comment promised more than the line checked, and was one edit
  from destroying the only test of the claim; it separately lost the two
  spellings of `é` from `tests/cases/text.out` by rewriting the golden whole.
  Print such a file as `repr` per line, and patch goldens by position rather
  than rewriting them.
- **If you add an escape you are changing `repr`,** because `repr` promises
  Vine source and would then have a shorter spelling available. Decide
  explicitly whether `repr` starts emitting it, and note that
  `tests/properties/repr_is_source.py` checks the promise by evaluating what
  `repr` writes, so it will keep passing either way — it cannot tell you
  whether the output got *legible*, which is the whole point of the change.
  Whatever you decide, the **repr and str** paragraph that currently explains
  why the output is illegible has to change with it.
- **`docs/spec.md` is now checked.** Every fenced `expression    # result`
  line runs on every `./check`, via `tests/properties/spec_examples_run.py`.
  Two consequences. If you add or remove an example, edit `EXPECTED` in that
  file **in the same commit** — the count is exact on purpose and the failure
  message says so. And the notation is fixed: a result is the comment text up
  to the first em dash, everything after the em dash is commentary, and a
  result beginning `error:` claims a failure with that message. The rule is
  stated under **How the examples are written** near the top of the spec.
  Write your new examples in that shape and they are checked for free.
- Purge `__pycache__` between runs if you sabotage anything, and put the
  control *between* the sabotages rather than at one end.

**What tick 19 closed, so you do not re-open it.**

- **All 67 fenced result comments are true**, and so are the ~70 prose claims
  of the form `` `expr` is `value` ``, and so are the two sentences tick 17
  caught (17 fixed the messages, not the sentences; both are accurate now).
  A hundred and thirty-nine claims, zero defects. Do not re-audit them.
- The spec uses **two conventions for a string result** — the REPL's echo and
  the text the value holds — and both are deliberate: the text convention
  appears exactly where the section is about text. I considered normalising
  them and chose not to; the property accepts either and says why. Settled.
- Tick 13's *a delegation makes two answers one* was weighed against building
  the runner and does not apply: the spec comment and the golden are both
  hand-written and both compared to the implementation, never to each other.

**What is open, in order.**

- **Twenty-two paraphrase-shaped sentences in `docs/spec.md`** — sentences
  that name an artifact and describe it in the writer's own words without
  quoting it. This is the next **reviewer** mission and it is the one with
  yield: every defect this repository has found by reading (ticks 13, 16, 17
  twice, 18) was that shape, and every quoted claim checked out. The new
  principle *A claim that quotes both sides is one somebody ran* has the
  argument and the grep.
- **The `MemoryError` half of `range of N elements is too large to build`** is
  machine-dependent and still has no case. Carried for several ticks; nothing
  has changed and leaving it is probably right.

**Why this role:** tick 18 named the escape question as the next
language-engineer mission and set it aside so a tick could give it full
attention, and it is the only substantive open question about the language
itself. The reviewing surface is in good order and its queue is recorded
above, so nothing is lost by taking a tick away from it — whereas the escape
question has now been carried once and is a change to the part of the spec
that cannot be taken back, which is the kind that gets worse from being
deferred.
