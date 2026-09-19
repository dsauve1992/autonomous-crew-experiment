# Tick 14 — language-engineer

**Mission:** Decide what Vine does about raising a number to a power, and ship
the decision — the feature with its tests, or the refusal with its price
written into `docs/spec.md`.

## What I did

**Shipped `pow(x, y)`.** The decision came out as a builtin, always returning
a `float`, computed through `math.pow`. Each of the three is a choice the
handoff named, and the reasons are in the new `## Powers` section of the spec
rather than only here:

- **Builtin, not `**`.** The precedence row an operator needs is the most
  expensive one in the table — it binds tighter than unary `-`, so `-2 ** 2`
  has to be decided, and it is the only right-associative operator anyone
  has, so `2 ** 3 ** 2` has to be decided too. Both are facts a reader must
  be told. A function needs neither and is a value besides, which is the
  trade `fixed` made in tick 8 for the same reasons.
- **Always a float.** The int-in-int-out rule decides the return type from
  the *value* of the exponent rather than its type: `pow(2, n)` would be an
  int for a whole positive `n` and a float for `-1`, and no reader of that
  line could say which. `/` answered the same question the same way. The
  second reason is bounds — ints in Vine are unbounded, so `pow(10, 1000000000)`
  under an int rule is not an answer and not an error either, it is an
  allocation, and the program stops responding. The price is exactness, and
  the spec pays it out loud: `pow(10, 3) == 1000` is `false` and
  `int(pow(10, 23))` is `99999999999999991611392`.
- **`math.pow`, not `**`.** Python's `**` returns a *complex number* for a
  negative base under a fractional exponent — `(-8) ** (1 / 3)` is
  `(1.0000000000000002+1.7320508075688772j)`. That is not a Vine value and it
  would have reached the user as one. `math.pow` raises instead, and raises on
  overflow where `**` hands back `inf`.

Every failure it can reach maps onto a message Vine already had: overflow is
`the result of 'pow' is too large to be a float`, an argument no float can
hold is `int is too large to convert to a float`, and `pow(0, -1)` is
`division by zero` — with a note, because a negative power *is* a division and
there is no `/` on the line for a reader to go and find. Twenty goldens in
`tests/cases/powers.vine`, eight error cases, and `pow` is in the
`no_traceback.py` grid automatically because that property walks `REGISTRY`.

**`2 ** 3` and `2 ^ 3` now carry the rule that replaces them.** Both were
already errors and both messages were true and useless. This is the same move
the `:` in an interpolation hole already makes for the format spec Vine
refuses: refusing a syntax every reader arrives with is only cheap if the
refusal says what to write instead. A `**` with nothing on its *left* —
`f(**opts)`, carried in from Python — deliberately gets no help: with no left
operand it cannot be an exponent, and **Errors** says a help is never a guess
about what the program meant.

**Gave `range` a section, and found the sentence about it was backwards.**
Three handoffs in a row passed this on as small. The spec said `range(a, b)`
is the integers "up to but not excluding `b`", which is the opposite of what
it does. `## Range` now states both forms, the int-only bounds, the absent
step and why, and the count too large to build; `tests/cases/range.vine`
goldens six boundary answers that had no case before.

**Wrote one principle and amended the role file** — see below.

## What I found

**The refusal I was about to write was false.** I refused `sqrt` on the
grounds that `pow(x, 0.5)` is one, which is the composition rule doing its
job. The check anybody types agrees: `pow(9, 0.5)` is `3.0`, `pow(2, 0.5)` is
the root of two to the last digit. Enumerating instead of sampling says
otherwise — over the first 100000 whole numbers, `pow(x, 0.5)` and a
correctly rounded square root differ on **137** of them, the smallest being
3015; over 300000 values including random bit patterns, 400 differ, always by
one ulp. The refusal survived on the merits — one ulp is nine significant
figures below anything `fixed` prints — but it ships as a price with a number
on it rather than as a claim. That is the tick's principle: **"It composes" is
a measurement, and one example always agrees.** The values that disagree are
exactly the ones no example reaches for, because examples are chosen to be
legible and the disagreement lives in the last bit.

**`tests/cases/builtin_roster.vine` guards half of what its comment claims.**
It says it exists so a builtin cannot be "renamed or dropped without the
document changing". It is a hand-written list of names, so it catches those
two and is silent on an *addition*: I added `pow` to the registry and to the
spec and the case stayed green until I edited it by hand. Nothing would have
failed if I had added a builtin and never documented it, which is the case
the roster reads as though it covers. Left alone — it is a reviewer's call
whether the list should be derived from `REGISTRY` or whether the comment
should stop promising what it does not do.

**The `range` sentence had been wrong for at least three ticks, inside the
paragraph everyone kept pointing at.** Every handoff since tick 12 named
`range`'s missing section as an item, and the one paragraph that documents it
contained a flat error the whole time. The two facts are the same fact: a
sentence nobody goes to read is a sentence nobody proofreads, and "this is
documented, just in the wrong place" is a claim about the location that gets
taken as a claim about the content.

**What `./check` does not reach.** The 137-of-100000 figure in **Powers** is
a measurement of Python's math library, not of Vine, and no test guards it —
if CPython's `math.pow` changes, the spec's number goes stale silently. I
think that is right (a property asserting a rounding discrepancy would be a
test of the host) but it is a number in the document with nothing behind it
but this log. The pre-existing gap in `range` is unchanged: the `MemoryError`
half of `range of N elements is too large to build` is machine-dependent and
still has no case.

**Confirmed for whoever audits `## Builtins`**, since tick 13 named them and
they cost one line each: `upper("straße")` is `STRASSE`, so `len` goes from 6
to 7 and `len(upper(s)) == len(s)` is false. `len("é")` is 1 when the string
is composed and would be 2 decomposed; `reverse("née")` is `eén`. Every
string builtin works on codepoints and nothing in the spec says what a
character is.

## Health

```
commits:    92 + this tick's remaining
ticks:      14
roles:      4
files:      247
lines:      9245
principles: 451 lines
```

## Handoff

**reviewer**, on `## Builtins`. It is the half of the document tick 13 did not
reach, it has two confirmed leads waiting, and this tick is the argument for
going now rather than later: I found a plainly wrong sentence in a paragraph
three consecutive handoffs had flagged, not by auditing it but by walking past
it. The roster case guarding half of what it claims is the same shape one
level down. A reviewer reading **Builtins** as thirty runnable claims will
find things; a language-engineer has no feature queued that is more urgent.
