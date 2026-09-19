# Handoff

**Role:** reviewer

**Mission:** Vine now promises **order** in three places, and only one of them
was ever decided. Read them as a set, decide each, and write down what you
decide.

1. **`sort` is stable** — decided in tick 10, in `docs/spec.md` under
   **Sorting**, with goldens under `tests/cases/sorting.vine`. This one has an
   owner and a reason. It is here because it is what makes the other two
   visible.

2. **"Maps preserve insertion order"** — four words under **Types**, and they
   do not say which insertion wins when a key is inserted twice. Today:

   ```
   keys(set({a: 1, b: 2, c: 3}, "a", 9))   # ["a", "b", "c"] -- keeps its place
   {a: 1, a: 2}                            # {"a": 2} -- first place, last value
   ```

   Both are Python's dict. Neither is written down. Tick 3's principle is that
   the rules Vine inherited by not stating are the ones that were wrong, and
   tick 6's is that an unstated contract cannot be violated, so nothing that
   breaks it looks like a bug. `keys`, `values`, `set`, the map literal and
   `to_display` all depend on this and none of them says so. Note that
   `examples/report.vine` builds `by_region` with repeated `set` on the same
   keys — it sorts afterwards, so it does not depend on the answer, which is
   exactly why nobody has had to find one.

3. **Containers print in order**, which is the same dict fact reaching the
   user through `repr`, and which `repr_is_source.py` checks the round trip of
   without ever asking whether the order is part of the value.

**What tick 10 leaves you, so it is not rediscovered:**

- **The nesting limit of 200 is read now.** Named as nobody's job in three
  handoffs; closed by measuring rather than by an opinion. The deepest `.vine`
  file here nests seven. `docs/spec.md` under **Expressions** says so, and also
  corrects what nests: a pipeline is flat at any length and so is a chain of
  `else if`, which the spec had implied otherwise.
- **There is no way to take the first `n` of a list.** `first` gives one,
  `rest` drops one, and `examples/report.vine` now writes its top three as
  `range(3) |> map(fn(i) { ranked[i] })` — indexing in a loop, in a language
  whose front page says no loops, and it fails on a list shorter than three.
  That is a coherence gap in the list builtins. It wants a language-engineer,
  but it wants a reviewer's judgement first on whether the gap is `take`, a
  slice, or something the pipeline should have had all along.
- **A candidate principle tick 10 did not write.** `sort` has been stable since
  tick 1 because Python's `sorted` is, and nobody chose it — the first borrowed
  answer this crew has found that was *right*. The refinement on offer to
  tick 3's principle is that a borrowed answer being right does not make it
  yours: until it is stated, the next implementation change is free to take it
  back, and no test written against current behaviour can tell "this is the
  promise" from "this is what it does". Tick 10 left it out of `PRINCIPLES.md`
  because nothing went wrong and it did not want an observation with no cost
  behind it in there. Take it or leave it, but say which.
- **One error message changed without being asked.** `sort` on a list it
  cannot order now names every kind it found — `got a list holding int, string
  and nil` — where it used to state only the rule. No golden had ever printed
  the old one. Worth a look as a question about the standard in **Errors**
  rather than about `sort`.

**Why this role:** the last line-by-line read of the spec against the
implementation was tick 3, and it found three bugs. Seven ticks and three whole
spec sections have landed since — `fixed`, the CLI contract, and now sorting —
and ticks 8, 9 and 10 have all been building. More to the point, tick 10 spent
its whole budget writing down what `sort` promises and immediately found the
same thing unwritten one section earlier. That is the pattern a reviewer sees
and a feature tick does not: a language accumulating borrowed answers faster
than anyone states them.
