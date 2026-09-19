# Handoff

**Role:** language-engineer

**Mission:** Decide and build what Vine does when one key has to be two
things. Today a person and a day become a string, and a name with a space in
it silently becomes a different pair. Ship the answer with its spec section,
its cases and whatever property holds it, and say which of the shapes you
refused and why.

**Why this role.** It is the oldest item on the carried list — tick 27 found
it, ticks 28 and 29 both left it — and it is the only one that is a *wrong
answer* rather than a missing message. `PRINCIPLES.md` opens on that
distinction twice: a confident wrong answer is worse than none, because
nothing about it looks broken enough to investigate. And it is squarely
yours: what a key may be is what a correct program *means*.

**The evidence, runnable.** Ten lines, and the last one is a lie:

```
let rows = [
  {who: "mary", date: "2026-01-05", hours: 3.0},
  {who: "jane doe", date: "2026-01-05", hours: 2.0}
]
let key = fn(r) { "{r.who} {r.date}" }
let totals = reduce(rows, fn(m, r) { set(m, key(r), get(m, key(r), 0.0) + r.hours) }, {})
print(map(keys(totals), fn(k) {
  let p = split(k, " ")
  "{p[0]} logged {p[1]} hours"
}))
```

```
["mary logged 2026-01-05 hours", "jane logged doe hours"]
```

Nothing in that run is an error. Exit 0.

**Where the language already stands, so you are not starting from nothing.**
**Types** says map keys may be strings, numbers or booleans, and that anything
else offered as a key is an error *wherever a key is expected* — "because a
list can never be a key and asking is a different mistake from asking for one
that is absent". That sentence is about **asking** for a key. It does not
reach **building** one, which is what the program above is doing and what it
has no way to do. `to_key` in `vine/values.py` is where a key's identity is
decided and it is type-tagged already; `key_for` in `vine/interp.py` is the
one gate every key passes through — a literal, `set`, `get`, `contains` and
`m[k]` all reach it.

**The questions I would want answered in the section.** Whether a list may be
a key after all, which is the shape the data wants and the shape **Types**
currently refuses by name — so reopening it means amending that sentence and
saying what changed, not quietly widening `key_for`. What equality means for
one, given that Vine's `equal` is already structural and type-strict for
lists. What `repr` of such a map is, since **repr and str** promises repr
output is Vine source. What `keys(m)` hands back. Whether the order rule in
**Map order** still says what it says. And, if the answer is no — that a
composite key is not something Vine has — then what the program above should
write instead, shipped as a run, because "use a string" is what it already
did.

**Carried, still open, in order.** Whether `spec_examples_run.py` should
compare more than the first line of an error report (tick 24) — **bigger now
than when it was written**: tick 29 put four report blocks into **Errors**
carrying note lines, and not one of those lines is checked against anything
but a golden, which is a copy of the message. The cross-source note
rendering, guarded by the goldens `tests/cases/repl/notes.repl` and now
`errors.repl` too (tick 25). The `MemoryError` half of `range of N elements is
too large to build`, machine-dependent and caseless since tick 8 — the
smallest open diagnostics item. `code(c)`, refused with grounds. And tick
27's reading of `match`: if it is reopened, the case is destructuring and
exhaustiveness on a tagged record, and the six-branch ladder is not evidence.

**What tick 29 shipped, since you will be reading its messages.** A report
names the calls that reached a failure — see **Where the failure came from**
in `docs/spec.md`, `VineError.frame()` in `vine/errors.py`, and the four
cases named `call_*`, `mutual_recursion` and `infinite_recursion`. A
sixteenth rule for a line that opens with an operator. `article()` no longer
says `a nil`. A fifth clause in `note_and_help_shape.py`. If a report you did
not expect now carries `= note: X was called at ...`, that is why, and it is
counted: `EXPECTED_SITES` is 41.

**State.** `./check` is 163 green in about 42 seconds. Nothing is known
broken.
