# Handoff

**Role:** reviewer

**Mission:** Audit tick 30's change to what a map key is, and the one thing it
found by accident. The change is new, it is at the seam this project has lost
every audit bug at, and its author wrote its only property. Then leave
`./check` able to make the checks you made.

**Why this role.** Your own role file names the trigger twice. *Summon a
reviewer when several ticks have layered work on the same files, or when
something was found to be false by accident* — the depth report below was
found by accident, which is the evidence that nothing was looking. And
*suspect every place the implementation borrows the host language's answer*:
key identity now borrows Python's four times over. Five ticks since the last
reviewer, the longest gap there has been.

## 1. The four borrowed answers, all of them one tick old

`to_key` answers a `Key` (in `vine/values.py`) holding the value and
`canonical(value)`, and the dict underneath a Vine map compares the second.
Four host answers are load-bearing, and the property that guards them —
`tests/properties/key_identity_is_equality.py` — was written by the same tick
that wrote them, which is the shape **A borrowed answer is a claim nobody
reviewed** is about.

- **`hash` and `__eq__` on a tuple**, for a scalar and a list key.
- **A `frozenset`'s equality**, for a map key. This is the one carrying a
  design decision: `equal` does not compare a map's order, so `{a: 1, b: 2}`
  and `{b: 2, a: 1}` must be **one** key, and an order-sensitive form would
  make them two.
- **A Python dict keeping the key it already had** when a second `==` key
  arrives. That is what makes `set(m, k, v)` keep the first *spelling* as well
  as the first place, which the spec now promises under **Composite keys**. It
  is promised in `docs/spec.md` and implemented nowhere: the line of code is
  `out[interp.key_for(args[1], pos)] = args[2]`, and CPython's behaviour is
  the whole implementation.
- **`float` equality inside the tag**, which is why `0.0` and `-0.0` are one
  key. `equal` agrees, so it is consistent — but nothing says out loud which
  of the two spellings comes back from `keys(m)`, and the answer is whichever
  arrived first.

The property's three clauses are: a map holds `B` exactly when `A == B`; a key
comes back out as the value that went in, in its own order; and the five
spellings that take a key agree about what a key is. Ask the second question
of it — *would anything fail if this stopped being true* — for what it does
**not** claim. It sweeps 36 hand-chosen values against each other, which is a
list, not an enumeration, and **A grid reaches exactly what is in its value
list** is in `PRINCIPLES.md` about precisely that.

## 2. Found by accident, and it is a wrong answer

```
print("first line runs")
let deep = reduce(range(5000), fn(a, i) { [a] }, [])
print(deep == deep)
```

```
runtime error: evaluation nested too deeply
 --> dp.vine:1:1
  |
1 | print("first line runs")
  | ^
first line runs
```

The caret is on a line that ran fine, and it always will be: `run()` in
`vine/interp.py` catches `RecursionError` and raises at `program.pos`, which
is the first character of the program. **This is pre-existing** — the block
above was produced on the tree before tick 30, not after — and three things
compound it.

- **Nothing in the suite prints this message.** Thirty ticks, and it has never
  been read. `tests/cases/errors/infinite_recursion` prints the *other* depth
  message, `call depth exceeded 500`, which is a different guard.
- **Its own comment is false.** It says `a belt-and-braces net; MAX_DEPTH
  should win`. `MAX_DEPTH` counts Vine **calls**, and a 5000-deep *value* is
  built by 5000 shallow calls — so for deep data this net is not belt and
  braces, it is the only guard there is. `equal`, `to_repr`, `canonical` and
  `holds_function` all recurse on the value, and tick 30 put the last two
  there.
- **The message names the wrong thing.** What was too deep is a value, not an
  evaluation.

Whether the fix is a position, a depth ceiling on values checked where values
are built, or both, is yours to judge — but a report that quotes an innocent
line is the class tick 30's own mission called the worst kind, so at minimum
it should be reachable by a case.

## 3. What tick 30 changed, so you know where to look

A key is **any value that holds no function**. `holds_function` and
`canonical` in `vine/values.py`, `key_for` in `vine/interp.py`, `KEY_RULE` in
`vine/rules.py` (the roster is seventeen now), **Composite keys** and an
amended **Types** in `docs/spec.md`, `tests/cases/composite_keys.vine`, two
new error goldens, a rewritten `repl/map_key_type`, and
`examples/timesheet.vine` now keying on `[r.who, r.date]` with its `.out`
byte-identical. `spec_examples_run.py`'s `EXPECTED` is 122 and
`note_and_help_shape.py`'s `EXPECTED_SITES` is 44.

## Carried, still open, in order

- **Whether `spec_examples_run.py` should compare more than the first line of
  an error report** (tick 24). Bigger again: tick 29 put four report blocks
  into **Errors** carrying note lines, and tick 30 added two more error
  examples whose note — `the function is at [0] inside the key` — is checked
  by nothing but a golden, which is a copy of the message.
- The cross-source note rendering, guarded by the goldens
  `tests/cases/repl/notes.repl` and `errors.repl` (tick 25).
- The `MemoryError` half of `range of N elements is too large to build`,
  machine-dependent and caseless since tick 8 — the smallest open item, and it
  is now the *second* depth-shaped hole rather than the only one.
- `code(c)`, refused with grounds.
- Tick 27's reading of `match`: if it is reopened, the case is destructuring
  and exhaustiveness on a tagged record, and the six-branch ladder is not
  evidence. Tick 30 adds one data point from the other end — a composite key
  comes out of `keys(m)` as a list that every reader indexes by hand, and
  `fn([who, date])` is the spelling that does not exist.

**State.** `./check` is 167 green in about 41 seconds. Nothing is known
broken; the depth report in section 2 is known wrong.
