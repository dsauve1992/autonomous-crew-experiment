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
