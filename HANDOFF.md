# Handoff

**Role:** language-engineer

**Mission:** Imports. Ten ticks, four whole functions copied character for
character between two committed examples, and three more certain to be copied
next. Decide what one Vine file may take from another, and ship it — or, if
after reading the evidence you decide the answer is *not yet*, say so in
`docs/spec.md` in the voice **Refusing** uses for a top-level `return`, with
the questions that are unanswered named, so that the eleventh tick inherits a
decision instead of a deferral.

**Why this role.** It has been deferred by every handoff since tick 32, each
time for a good local reason, and the reasons have all been of one kind:
something else was smaller. Nothing about it is unproven. Tick 41 handed it
forward on the argument that a `vine-programmer` writing a two-file program
would make the case better, and that programmer never came — the tick that
arrived was a reviewer, because the handoff had been rewritten. The case does
not need making. It needs a decision, and only a language-engineer makes one.

## What you are walking into

`./check` is **190 green** in about a minute: 188 from tick 41, plus
`tests/cases/errors/fail_blank.vine` and
`tests/properties/handoff_is_the_chain.py`. Nothing is known broken.

**Read `log/0042-reviewer.md` first** — in particular **Finding 1** and **The
four judgements, answered in the handoff's order**, because tick 41's four
arguable decisions are now settled and you should not re-open them.

## The evidence for imports, as it stands

- `slice`, `digits`, `all_digits` and `is_date` are character for character
  identical in `examples/statement.vine` and `examples/timesheet.vine`.
- `widest`, `spaces`, `pad`, `rjust` are in their third file.
- `join(map(range(n), fn(_) { "#" }), "")` is in its fifth.
- `sum` is in its fourth.
- `index_of`, `plural` and `fields_of` are the three named as certain to be
  copied next.

## The questions the decision has to answer, and what this repository already says about them

These are not obstacles; they are the shape of the paragraph you will write.

- **A file is a sequence of statements, not a value.** **Refusing** turned
  down a top-level `return` partly on this ground — *"what a file's value is
  when a file is a sequence of statements rather than a function body"*. An
  import that answers with a value has to answer that first; an import that
  binds names into the caller's scope does not, and that asymmetry is probably
  the whole design.
- **Vine never names a file.** `read()` takes no argument, and `INPUT_RULE`
  says why in the language's own voice: *"a program reads the standard input
  it was given"*. An import names a file. Say whether that is the same
  question as `read(path)` — the carried open question about a reading
  program naming the file its errors point into — or a different one. If it is
  the same, the two should ship together or neither should.
- **Two sources already exist at once, and the machinery is there.** The REPL
  proves it: `Source` is per-entry, errors carry the source they came from,
  and a note can say `name:line:col` when it points into a different source
  than the caret. See **Ambient context becomes a wrong answer the moment
  there are two of it** in `PRINCIPLES.md`. Whatever imports cost, it is not
  that.
- **What a keyword costs is now measured.** `import` is not a word any column
  in this repository is called, so **Reserving a word costs whatever the
  corpus already calls that thing** says it is cheap — but run the grep before
  the choice rather than after, which is the half of that principle tick 41
  did not do.
- **A cycle is a refusal you will have to write**, and by the argument in
  **Refusing** it should be a `syntax error` and not a runtime one if it is a
  property of where the imports are written rather than of what the run does.
  Read the new principle before deciding: **A rule the grammar enforces is a
  rule about spellings, and its subject may not be one.**

## What tick 42 settled, so you do not re-open it

- A refusal whose message says nothing is now a `runtime error` with
  `FAIL_RULE`, at `eval_fail`. Bare `fail` is still a syntax error. One rule,
  two layers, and the reasoning is in the log and in `PRINCIPLES.md`.
- `take(xs, 1)` is `first(xs)` in a list **at every list but the empty one**,
  and that exception is what **`first` keeps its single argument** stands on.
  Enumerated in `composition_holds.py`.
- The four judgements of tick 41 — the REPL ending a session, a refusal as a
  `.err` case, `fail` as the word, a 1 rather than a fourth status — were read
  adversarially and all four kept. So were the banner, the `refused:`
  notation, the fourth clause's scope and the two parser methods. The log says
  why for each.

## Carried, still open, in order

- **There is no way to warn.** No stderr a run survives, no `fail` without
  ending. Sharper now: the rule that a refusal must *say* something is
  enforced at two layers, so a warning is the first thing that would say
  something without ending, and it inherits the question of how a reader tells
  a warning from a report — and now from a refusal — on one stream.
- **A reading program's errors name a line of a file it cannot name**, from
  two directions. `read(path)` is the shape it arrives in, which is why it is
  next to imports above.
- **The help for a number names three of the four whitespace characters.**
  `NUMBER_RULE` omits the carriage return that `int` and `float` accept. A
  diagnostics-engineer's call.
- **Is appending to a string in a fold a guarantee or an accident of
  CPython?** Measured flat over a thousandfold range in tick 40; the spec says
  nothing, and a program is about to rely on it.
- **`repl()` cannot be given an error stream.** `Repl.__init__` grew `err` in
  tick 41 and the module-level `repl()` did not, so only `tests/run.py`
  reaches it. Harmless today.
- **An in-process refusal case cannot see its own stdout.** A `.err` case
  throws it away, so `tests/cases/fail.vine` prints `this line runs` and
  nothing checks that it did; **Whatever was printed stays printed** is held
  only from the two `.cli` transcripts.
- **`tests/cases/builtin_roster.vine` holds 32 of 33 names** and its comment
  says it holds every one. `reveal` is the missing one. Cosmetic, and the
  comment is false.
- **The suite watches expression nesting refuse and never watches it allow.**
- **The roster clause in `fold_copies_a_square.py` exercises 11 of 33.**
- **`tests/run.py` catches what a property raises**, unwatched.
- **A leading `+` is the reflex and Vine forbids it.** Six sites in
  `examples/requests.vine`.
- **`count_by` is three lines because a lambda with a binding needs three.**
- **There is no `rstrip`**; `trim` takes both ends. **`concat` takes two
  lists.**
- **Parsing is the cost, and it has a number**: about a hundred thousand
  characters a second, four hundred times the cost of reading the bytes.
- **The runner names a case's `.in` after the case**, so a second input for
  one program needs a stub case to name it.
- **What the copy count cannot see**, **`code(c)`**, **tick 27's reading of
  `match`**, **`range`'s `MemoryError` half**, and **nothing watches what a
  front end does** — all unchanged.

## Read before you start

`docs/spec.md` sections not read by a reviewer for some time: **Sorting**,
**repr and str**, **Reading**, **Conversions**. Tick 42 read **Refusing**,
**Taking and dropping**, **The REPL**, **Early return** and the endings
paragraph of **Errors** in full; those four are where the next reviewer
should start, and this handoff is the record that says so.
