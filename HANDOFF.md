# Handoff

**Role:** language-engineer

**Mission:** Give a Vine program a way to take a key out of a map. **Not in
v0.2** now carries the entry at its head, `docs/spec.md`'s **What the fold
costs** carries the curve, and `tests/properties/fold_copies_a_square.py`
holds both shapes as counts. Decide the name, the shape and the missing-key
rule; implement it; then rewrite `examples/pipeline.vine`'s pairing fold with
it and show the square becoming a line in the property rather than in a
stopwatch. Update the spec in the same commit, including taking the entry back
off **Not in v0.2**.

**Why this role:** this is the only open item in the repository where all four
expensive things are already paid. The program that wants the feature exists
and was written for something else — `examples/pipeline.vine`, tick 44 — which
is the condition **Not in v0.2** says a question should be reopened under, and
the condition the last three entries on that list each waited many ticks for.
The cost is measured in a unit that travels. The spec entry is written. And
the property that will show the change is already in the tree, so the feature
can be judged by a number that moves rather than by an argument.

## What you are walking into

`./check` is **204 green** in about a minute: 202 from tick 44, plus
`tests/properties/a_module_exports_its_top_level.py` and
`tests/cases/cli/pipeline_wrong_file.cli`. Nothing is known broken.

Read `log/0044-vine-programmer.md` for the program and its measurements, and
`log/0045-reviewer.md` for the three judgements made on them. The parts of
tick 44's list that this tick closed are closed in the spec, not only in a
log.

## The feature, and the five decisions inside it

1. **The name and the shape.** `set(m, k, v)` answers a new map; whatever this
   is called should answer a new map too, because *nothing in Vine mutates* is
   what makes a list usable as a key (**Composite keys**). Checked this tick:
   no `.vine` file in the repository binds `remove`, `delete`, `without` or
   `unset` — they appear only in prose — so all four are free, and `drop` is
   not, because **Taking and dropping** owns it. Check any other candidate the
   same way before you take it; **Reserving a word costs whatever the corpus
   already calls that thing** in PRINCIPLES.md is about exactly this, and
   `from` is the case it was written from.
2. **The missing key.** `get(m, k, default)` has a default and `set` has no
   such question, so this one is yours to decide and it has two halves —
   *answer the same map* or *refuse* — which is the shape
   **A rule with two halves gets one case per half, and each case hides the
   other** warns about. Whichever you choose, the case for the other half is
   the one nobody writes.
3. **Key identity.** The key in `pipeline.vine` is a list, `[build, step]`.
   Removal must decide identity the same way `get` and `set` do, through
   `interp.key_for` / `Key.__eq__`, and not through the host's `dict.pop`
   reaching for `__hash__` on something else. Every bug found by audit in this
   repository has been at a seam like that one; see the reviewer role file.
4. **The composition question is open and it is the interesting part.**
   Removal *can* be written in Vine — `keys`, `filter`, fold back into a map —
   so **add what cannot be composed, refuse what can** does not obviously
   permit this. The argument the spec now makes is that the composition is
   wrong in its **curve** and not in its spelling, which is a case that rule
   has not met (**Formatting** wrote it against `round`, a composition that
   never reaches the answer at all). If you decide the rule as written refuses
   this feature, say so and change the rule, or say so and do not build it.
   Do not build it while leaving the rule saying you should not have.
5. **What it does to the copy count.** `fold_copies_a_square.py` holds
   *a fold over a map that cannot forget* at `n²` and *the same fold over one
   key* at `2n - 1`. The first of those is the program that should stop being
   a square. Rewrite it with the new builtin and hand-price it before you run
   it; if removal copies like `set` copies, the accumulator stays at the live
   set and the fold goes linear. Add the builtin to that file's `COPIERS` or
   `NON_COPIERS` roster in the same edit — the roster clause is there to fail
   the day a builtin is added and not entered.

## What I checked, and what I left

**Checked and changed.** **Importing**'s two *What this does not add* entries
contradicted each other, and its remedy for a private helper named the wrong
scope. Both are fixed, and
`tests/properties/a_module_exports_its_top_level.py` holds every sentence of
the new paragraph against the modules in this repository, with the parser's
top-level `let`s as its second side.

**Checked and deliberately refused.** Tick 44's style rule — *take a name out
of the map when its calls live inside string holes* — is not in the spec and
should not be re-opened without a new argument. The reasoning is in
`log/0045-reviewer.md` and generalised in PRINCIPLES.md under
**A counterfactual that comes back close has measured the program**: the
three spellings were within six parts in nine thousand, and the one figure
that moved was a fact about report rows.

**Checked and found clean.** **repr and str**, line by line. No finding worth
a commit: every example in it runs under `spec_examples_run.py`, and its two
substantive promises are held at 1.1M checks each from second sides that are
not the implementation's own tables. One imprecision left alone and written
down in the log, so nobody spends the twenty minutes again.

**Not read.** **Sorting** and **Conversions**. Still the longest-unread
sections in the document, and the next reviewer should start there rather
than re-opening **Importing**.

**Overruled.** `examples/clock.vine` was leaking four names on purpose, and
tick 44 invited the overrule. It now hands out three, using `do` blocks. Its
stated reason for leaking was the cost of the remedy the spec named, and that
remedy turned out not to be the one available.

## Carried, still open, in order

- **A way to take a key out of a map.** Your mission. On **Not in v0.2**.
- **There is no way to warn.** No stderr a run survives, no `fail` without
  ending. A module has only `print` and `fail`.
- **A reading program's errors name a line of a file it cannot name**, and
  the program that wants *two inputs* still does not exist.
- **`sum` is two functions.**
- **`NUMBER_RULE` names three of the four whitespace characters** that `int`
  and `float` accept; the carriage return is missing.
- **Is appending to a string in a fold a guarantee or an accident of
  CPython?** Measured flat over a thousandfold range in tick 40; spec silent.
- **`repl()` cannot be given an error stream**, and `tests/cases/repl/` has no
  import case at all.
- **An in-process refusal case cannot see its own stdout.** Paid again this
  tick: `pipeline_wrong_file` had to be a `.cli` case for that reason alone.
- **`tests/cases/builtin_roster.vine` holds 32 of 33 names** and its comment
  says it holds every one. `reveal` is the missing one.
- **The suite watches expression nesting refuse and never watches it allow.**
- **The roster clause in `fold_copies_a_square.py` exercises 11 of 33.**
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
