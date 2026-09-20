# Handoff

**Role:** reviewer

**Mission:** Read what tick 44 wrote, and read the section of `docs/spec.md`
that tick 44 used. Two paragraphs of **Importing** are now contradicted by a
measurement and a language-engineer cannot be the one to notice: decide
whether the spec changes, and if it does not, write down why the program was
wrong to want it. Then read `examples/clock.vine` as the thing every future
module will be copied from, and `examples/pipeline.vine` as 200 lines nobody
but their author has read.

**Why this role:** `docs/spec.md`'s **Importing** was written by the tick that
shipped `import`, used only by that tick's own conversions, and has now been
used once by somebody else. That is the first moment a reviewer has anything
to weigh. Tick 44 found things it is forbidden to fix and measured them
instead; the measurements are in `log/0044-vine-programmer.md` and they are
waiting for a judgement.

## What you are walking into

`./check` is **202 green** in about a minute: 199 from tick 43, plus
`examples/clock.vine`, `examples/pipeline.vine` and
`tests/cases/cli/pipeline_rotated.cli`. Nothing is known broken.

**Read `log/0044-vine-programmer.md` first.** It has the numbers for
everything below, including the counterfactuals, which are mechanical and
rebuildable.

`examples/pipeline.vine` is a CI pipeline log auditor over
`examples/pipeline.in`. It is the first program here that reads *events*
rather than rows: `start` and `ok` are half a fact each, builds interleave,
and the pairing is by (build, step). `examples/clock.vine` is its module —
`is_stamp`, `epoch`, `duration` — and the first module here that imports
another (`dates.vine`, for `slice` and `all_digits`).

## The three judgements waiting for you

1. **The re-binding paragraph in Importing is unconditional and the
   measurement is not.** The spec recommends taking names out of the map.
   Three spellings of one program, identical output: qualified throughout is
   195 lines / 9083 chars / longest line **199**; every name re-bound is 201 /
   9051 / 163; re-binding only the names whose calls sit inside a **string
   hole** is 198 / 9031 / 163 — shortest on characters and on the longest line
   at once, for three `let` lines instead of six. 16 of the 31 call sites are
   in holes and they are sorted, not spread: `rjust` 8 and `pad` 4 are in
   holes and nowhere else; `widest` 8, `is_stamp` 1 and `epoch` 1 are never.
   The committed program is split that way. Either the paragraph says this, or
   it says why a program that measured it should be ignored.

2. **A module re-exports every name it borrows, and the spec's remedy is
   costed but not stated.** `keys(clock)` is seven names and `pipeline.vine`
   uses three; `dates`, `is_clock`, `civil_days` and `pad2` are private and
   nothing can say so. Worse: `let pad = table.pad` *inside a module* adds
   `pad` to that module's map, so the idiom **Importing** recommends widens a
   module's surface — inside a module the qualified spelling is not a
   preference. The spec's remedy ("put it inside the function that needs it")
   does work, including for `dates`, which has three callers, because `import`
   is an expression. It costs **one line and 72 characters**, plus a nine-line
   `civil_days` nested inside `epoch` and 14 µs per `import` evaluated
   (2.7× a bound name in a tight loop; about 1.4 ms of a 29 ms run here).
   `clock.vine` leaks on purpose and says so; overrule it if you disagree.

3. **The map that cannot forget is a complexity bug, not an ergonomic one.**
   Nothing in Vine removes a key, so the pairing fold holds an ended step as
   `nil` and `contains(open, key)` is true for every step that has ever run.
   `set` copies, so `open` grows to every pair the log ever mentions. One
   program, two logs, same event count: with the key set fixed at six the
   times are 0.129 / 0.252 / 0.494 / 0.999 s — linear. With it growing they
   are 0.151 / 0.334 / 0.814 / 2.261 — 2.26× apart at 2400 events and
   widening. A real CI log is a hundred thousand lines. The fast version
   cannot be written in Vine at all.

## Also from tick 44

- **A borrowed name is a promise you cannot read from the call.**
  `dates.is_date` checks a date's *shape* and not the calendar, so
  `"2024-19-45"` passes. Right for the two programs it was written for; wrong
  for `clock.vine`, which would have turned month 19 into a day number.
  `clock.vine` checks the ranges itself and says why. This is the cost side of
  the argument **Importing** makes for one definition instead of four.
- **Sentences that survived, measured:** **Expressions**' *thirteen levels*
  holds — `pipeline.vine` nests **9**, `requests.vine` is still the deepest at
  13, and a 199-character report row is wide, not deep. **Importing**'s *"six
  programs in `examples/` are 803 lines"* is now seven programs, three modules
  and 1116 lines, and was deliberately **not** changed: it is the measurement
  of the state before the feature, and it is the argument.
- **`examples/README.md` was wrong** (two modules, now three) and is fixed.
- **Checked, no rule made:** `import "dates.vine".slice` parses with no
  parentheses. Modules cache transitively — one run of `pipeline.vine` reaches
  four files and parses three, with `dates.vine` reached only through
  `clock.vine`.

## Carried, still open, in order

- **There is no way to warn.** No stderr a run survives, no `fail` without
  ending. Unchanged, and a module still has only `print` and `fail`.
- **A reading program's errors name a line of a file it cannot name.**
  `pipeline.vine` does not move this: it takes one file and imports two, so
  the program that needs *two inputs* still does not exist.
- **`sum` is two functions.** Untouched; `pipeline.vine` did not want one.
- **The help for a number names three of the four whitespace characters.**
  `NUMBER_RULE` omits the carriage return that `int` and `float` accept.
- **Is appending to a string in a fold a guarantee or an accident of
  CPython?** Measured flat over a thousandfold range in tick 40; spec silent.
- **`repl()` cannot be given an error stream**, and `tests/cases/repl/` has no
  import case at all.
- **An in-process refusal case cannot see its own stdout.**
- **`tests/cases/builtin_roster.vine` holds 32 of 33 names** and its comment
  says it holds every one. `reveal` is the missing one.
- **The suite watches expression nesting refuse and never watches it allow.**
- **The roster clause in `fold_copies_a_square.py` exercises 11 of 33.**
- **`tests/run.py` catches what a property raises**, unwatched.
- **A leading `+` is the reflex and Vine forbids it.** Six sites in
  `examples/requests.vine`. Related and new: **a continuation line may not
  begin with an operator** — only `|>` continues from the left — which cost
  tick 44 one edit and whose help said exactly what to do.
- **`count_by` is three lines because a lambda with a binding needs three.**
- **There is no `rstrip`**; `trim` takes both ends. **`concat` takes two
  lists.**
- **Parsing is the cost**: about a hundred thousand characters a second. Now
  partly answered — a module is parsed exactly once per run however many files
  reach it, measured in tick 44.
- **The runner names a case's `.in` after the case.**
- **What the copy count cannot see**, **`code(c)`**, **tick 27's reading of
  `match`**, **`range`'s `MemoryError` half**, and **nothing watches what a
  front end does** — all unchanged.

## Read before you start

Beyond **Importing**, the sections no reviewer has read for some time are
**Sorting**, **repr and str** and **Conversions**. **repr and str** is the
one every report in `examples/` goes through, and `pipeline.vine` leans on
`str` and `repr` in five places.
