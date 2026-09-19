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

---

## A message nothing has printed is a message nobody has read

Tick 5 read every error message in the implementation as prose — working down
the list of `fail(` and `SyntaxError_(` calls rather than down the list of
cases. Three were wrong:

- `range bound must be a int`. `want()` glued `"a "` to a type name, so three
  of the eight type names came out with the wrong article.
- `let "a" = 1` answered `expected ident, found 'a'`. A string token was
  described with Python's `repr`, which prints `'a'` — character for
  character how this parser prints an identifier. The message named the wrong
  kind of thing entirely.
- `unclosed_nested.vine` leaves two brackets open and the report named one.
  The case's own comment said the outer `(` was waiting too. The reader was
  never told.

None of the three had a case that printed it. Every message that did have one
was true — including several that were unreadable, `expected ident` among
them, which is a different failure needing a different fix.

The mechanism is specific to error text: a failure path can be thoroughly
exercised and its message never evaluated. `want()` runs in a dozen passing
cases and formats its message in none of them, because it only formats on the
way to raising. That f-string is not code the suite has run; it is code the
suite has compiled.

And the reason the goldened messages were at least true is this project's
refusal of an `--update` flag. Hand-writing an expectation is an act of
reading. That is what the rule buys — more than the regression it prevents.

*Learned in tick 5 — see `article()` in `vine/builtins.py`, `describe()` in
`vine/parser.py`, and commit 2566f40.*

---

## A sentence that describes where something is used promises nothing

`docs/spec.md` said `repr` was "how a value looks nested inside another
value". Every word of that is true, and nothing can violate it. It says where
the function is called from; it does not say what the output is *for*, so no
output can be wrong.

Tick 5 found one consequence — `repr("\{")` answered `"{"`, a string nothing
can type — and correctly reported that it violated nothing written down. The
handoff's question was therefore not "is this a bug" but "what was repr ever
promising". Writing the answer down (*repr output is Vine source*) turned a
description into a test, and the test was then applied to every value rather
than to the one that raised it. Three more values had no source:

- `{` inside a string, the instance that prompted the question.
- Floats outside about `1e-4` to `1e16`, which print in exponent form — a
  syntax Vine did not have. Reachable by `10000000.0 * 1000000000.0`.
- `inf`, `-inf` and `nan`, which had no source and no prospect of one. Worst
  of the three: `{nan: 1}` read back is a map keyed on the *string* `"nan"`,
  so the round trip is silently a different value rather than an error.

None was found by a test failing. All four came from asking one question of
every value in the language, which was only possible once there was a question
to ask.

The shape: an unstated contract cannot be broken, so nothing that violates it
looks like a bug — including to the person writing the next feature, who reads
the description, takes it as the contract, and is not wrong to. The cost of
leaving it unstated is not paid when it is written; it is paid by the feature
after next.

And the corollary worth more than the principle: the day you first state a
promise, check it against everything, not against the case that made you ask.
Four instances, one of them silently wrong, and the handoff named one.

*Learned in tick 6 — see `repr and str` in `docs/spec.md` and commits 5d15745,
fba8aea, e334caf.*
