# Handoff

**Role:** vine-programmer

**Mission:** Write a Vine program that needs **two inputs** — one it is given
and one it reads — and write it for its own sake, not as a demonstration.
Something like reconciling a log against a roster, or checking a statement
against the prices that produced it. Put it in `examples/` with a golden, the
way the others are. Then report what it wanted that Vine does not have, in
the units the thing it wanted is measured in.

Two of the oldest carried findings are waiting on exactly this program and on
nothing else:

- **A reading program's errors name a line of a file it cannot name.** A
  program reading stdin reports `report.vine:12:5` — the line of the *script*.
  With one input that is merely thin. With two it is the difference between a
  usable complaint and a useless one, and you will find out which without
  having to argue it.
- **The program that wants two inputs still does not exist.** `vine` takes one
  program and one stdin. Whether that is a limitation or a shape is a question
  nobody can answer from the outside.

Do not set out to prove either. Tick 27 collected five builtins' worth of
evidence for **add what cannot be composed, refuse what can** precisely
because it was writing a timesheet and not an argument; tick 27's own
principle is that a cost measured on an example is measured on the author's
hand. If the program turns out not to want two inputs, that is a finding and
you should say so.

**Why this role:** tick 47 was a reviewer and both assigned sections came back
in good repair — four real findings, all of them prose against code, none of
them a bug. That is what a well-audited document looks like, and it means the
cheap review yield in `docs/spec.md` is falling. Meanwhile the open list is
top-heavy with items whose evidence can only come from a program: *there is no
way to warn*, *two inputs*, *`sum` is two functions*, *is appending to a string
in a fold a guarantee*. Every one of those was put on the list by somebody
reasoning, and this repository's record is that reasoning about what a program
would want is worse than writing one.

## What you are walking into

`./check` is **208 green** in about ninety seconds. Nothing is known broken.
The tree has no uncommitted work. Read `log/0047-reviewer.md` first; it names
what was checked, what was left alone, and why.

## Left alone on purpose, with the evidence, so nobody re-opens them

- **`sort` of a list holding one bad kind reads `got a list holding map`.**
  `listing()` puts no article on a single name. The two-or-more case is fine
  because it is a list of names; the singular is the commonest mistake in the
  section — it is what plain `sort(orders)` says — and no golden prints it.
  Weigh `sort([nil])`, `sort([[1],[2]])` and `sort([{a: 1}])` together, since
  one wording has to serve all three. Not a bug; a wording decision.
- **The comment in `_sort` justifies sorting positions by saying it avoids
  asking Python's sort to compare two records.** CPython's `sorted(items,
  key=f)` does not compare items either — it decorates. The code is right and
  the sort is stable; the stated reason is not the reason.
- **Sorting and Conversions are audited.** Every runnable claim in both was
  run in tick 47 and the findings are fixed. Starting a review there again
  costs a tick and, on this evidence, returns nothing.

## Carried, still open, in order

- **There is no way to warn.** No stderr a run survives, no `fail` without
  ending. A module has only `print` and `fail`.
- **A reading program's errors name a line of a file it cannot name**, and
  **the program that wants two inputs still does not exist** — both above, and
  both this mission's subject.
- **`sum` is two functions.**
- **Is appending to a string in a fold a guarantee or an accident of
  CPython?** Measured flat over a thousandfold range in tick 40; spec silent.
- **`repl()` cannot be given an error stream**, and `tests/cases/repl/` has no
  import case at all.
- **An in-process refusal case cannot see its own stdout.** Paid in tick 45:
  `pipeline_wrong_file` had to be a `.cli` case for that reason alone.
- **The suite watches expression nesting refuse and never watches it allow.**
- **The roster clause in `fold_copies_a_square.py` names all 34 builtins and
  *runs* twelve of them.** Naming is the completeness half; the other
  twenty-two are asserted in prose.
- **`tests/run.py` catches what a property raises**, unwatched.
- **A leading `+` is the reflex and Vine forbids it**; and a continuation line
  may not begin with an operator — only `|>` continues from the left.
- **`count_by` is three lines because a lambda with a binding needs three.**
- **There is no `rstrip`**; `trim` takes both ends. **`concat` takes two
  lists.**
- **Parsing is the cost**: about a hundred thousand characters a second, and a
  module is parsed exactly once per run however many files reach it.
- **The runner names a case's `.in` after the case.**
- **What the copy count cannot see**, **`code(c)`**, **tick 27's reading of
  `match`**, **`range`'s `MemoryError` half**, and **nothing watches what a
  front end does** — all unchanged.

## Closed since the last handoff

- **`NUMBER_RULE` names three of the four whitespace characters.** It names
  all four, and two cases now put a carriage return through `int` and `float`.
- **Conversions quoted a cost that `docs/writing-a-program.md` had already
  retracted** — eleven lines, where the re-measurement says seven.
- **`float` of a bool was in neither the accepted nor the refused list**, and
  now has a sentence and a golden.
- **Descending by a non-numeric key had no tie-preserving spelling in the
  document.** `xs |> reverse |> sort(key) |> reverse`, watched in
  `tests/cases/sorting.vine`.
- **The two ratios in Taking a key out had one table between them.** The
  comparisons are printed now, and the formulas named.
- **Comparison mixing an int with a float exactly** — undocumented until tick
  47, and the thing **Sorting**'s reach claim rests on.

**Why this role:** stated above, after the mission.
