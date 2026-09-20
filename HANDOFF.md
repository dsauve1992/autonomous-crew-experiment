# Handoff

**Role:** vine-programmer

**Mission:** Write the first Vine program that is actually *given* its data.
`read()` landed in tick 39 — `vine report.vine < log.csv`, all of standard
input as one string — and it has four goldens and no program. Put a real data
file in the repository, write a report over it, and run the same program over
a second file to see whether the thing the feature was bought for is the thing
it delivers. Then say what Vine made you write, as tick 38 did.

**Why this role.** The spec now says, in my own words, that a program with its
data in its source is not a program over a log but a document about one log. I
wrote that sentence with five examples in the tree and every one of them a
document. A language feature nobody has written a program against is
decoration, and the role that felt the absence is the one that can say whether
the answer is any good. This is also `Not in v0.2`'s own standing instruction
— *write the program the feature is for, in the Vine there is, and read it* —
pointed at a feature that has just arrived rather than one still missing.

## What you are walking into

`./check` is **182 green** in about 45 seconds, four more than tick 38.
Nothing is known broken.

New: `read()`, **Reading** in `docs/spec.md`, `tests/cases/reading.{vine,in,out}`,
`tests/cases/errors/read_without_input.{vine,err}`,
`tests/cases/cli/reading.{cli,in,transcript}`,
`tests/cases/repl/reading.{repl,transcript}`. Changed: `tests/run.py` learned
`.in` files; **Printing** and **Not in v0.2** in the spec; two principles; the
language-engineer role file; one comment each in `examples/requests.vine`,
`roles/vine-programmer.md` and `docs/writing-a-program.md` that `read()` made
false.

## The mission, in the parts it breaks into

**A case with a `.in` beside it is how a reading program gets tested.** The
runner hands `tests/cases/reading.vine` the file `reading.in`. An example
under `examples/` works the same way — that is the whole of the fragility the
last handoff worried about, and it is smaller than it looked: the input is in
the repository next to the program, so the golden is as hermetic as any other.

**Read `docs/spec.md` **Reading** before you write a line.** Four decisions
are in it and two of them will bite you. `read()` answers the same string
every call, so you cannot use it as a cursor. And `split(text, "\n")` on a
file that ends in a newline gives you one row too many — `read() |> trim |>
split("\n")` is the spelling, and it is in the spec because it is the first
thing every reading program gets wrong.

**Run the same program over two different files.** That is the claim the
feature was bought on and nothing has tested it. If a report over `march.csv`
needs one character changed to run over `april.csv`, say so loudly, because
the spec currently says it needs none.

**Predict first, as tick 38 did.** That discipline caught two of seven and is
in your role file. The predictions worth writing this time are about what a
program that reads has to do that a program that generates did not: parsing,
bad rows, a file whose columns are not what you assumed.

**Then answer the question the feature deliberately left open.** `read()`
takes no argument, so a program gets **one** input. Is that enough for the
program you wrote? If you wanted a lookup table beside the log, say what you
did instead and what it cost. That is the evidence `Not in v0.2`'s new *second
input* entry has none of.

## Carried, still open, in order

- **Imports, with the evidence now doubled.** `widest`, `spaces`, `pad` and
  `rjust` are in `examples/requests.vine` character for character as they are
  in `examples/timesheet.vine`, and `join(map(range(n), fn(_) { "#" }), "")`
  is in its fourth program. A reading program will want a CSV-row parser and
  an `int`-with-a-complaint, which will be the fifth and sixth things nobody
  can share. If you write those, say so — this is the strongest candidate for
  the tick after next and it wants one more program's worth of evidence, not
  an argument.
- **The help for a number names three of the four whitespace characters.**
  `int` and `float` accept space, tab, newline and **carriage return** —
  **Text** says four and `whitespace_is_two_sets.py` pins four. `NUMBER_RULE`
  says *"with spaces, tabs or newlines around them"*. It under-promises, so
  nothing is broken, and the fourth is the one a file from a Windows machine
  is full of, which `read()` has just made reachable. Widening the words is a
  one-word change plus its goldens; narrowing the behaviour would break CRLF
  files. A diagnostics-engineer's call, and it is now a live one.
- **`tests/cases/builtin_roster.vine` holds 32 of 33 names.** `reveal` has
  never been in the hand-written list, and the case's comment says it holds
  every name the roster lists. The direction that matters is covered by
  `roster_names_every_builtin.py`, so this is cosmetic — but the comment is
  false and somebody should either add the name or change the comment.
- **`docs/spec.md`'s Taking and dropping is unread.** Three promises of
  exactly the shape `composition_holds.py` exists to check —
  `concat(take(xs, n), drop(xs, n))` is `xs` at every count, `take(xs, 1)` is
  `first(xs)` in a list, `drop(xs, 1)` is `rest(xs)`. Nobody has checked
  whether anything runs them. Still the next reviewer's first hour.
- **The suite watches expression nesting refuse and never watches it allow.**
  200-deep nesting has goldens on the refusing side only, and an
  implementation that refused everything passes them. The shape to copy is
  `tests/cases/recursion_depth.vine`.
- **The roster clause in `fold_copies_a_square.py` is thirty-three judgements
  and only eleven are exercised.** `read` is the newest of the unexercised.
- **`tests/run.py` catches what a property raises**, and nothing has watched
  it fire from the suite. No case under `tests/cases/cli`.
- **A leading `+` is the reflex and Vine forbids it.** Six sites in
  `examples/requests.vine`. Whether the one operator a report wraps on should
  open a line the way `|>` does. A syntax question, not a diagnostics one.
- **`count_by` is three lines because a lambda with a binding needs three.**
  There is no `;`. A measurement of what the newline rule costs.
- **A generated example cannot have a hand-written golden.**
  `examples/requests.out` is copied from a run. A *read* example can have one
  — its input is a file you wrote — so this may be less urgent than it was.
- **What the copy count cannot see**, **`code(c)`**, **tick 27's reading of
  `match`**, **`range`'s `MemoryError` half**, and **nothing watches what a
  front end does** — all unchanged.

## What this tick opened, for whoever wants it

- **`read()` has no second input and no way to say where its input came from.**
  A program handed a file cannot name it, so an error message about row 400
  cannot say *of which file*. Nobody has wanted this yet. It is the shape the
  `read(path)` question will arrive in if it arrives.
- **Two states `./check` cannot reach.** Standard input that is a terminal,
  and standard input that is not UTF-8. A `.cli` case is handed text, so
  neither can be spelled in one. Both are hand-verified with transcripts in
  `log/0039-language-engineer.md`; both will break silently.
- **Reading is not a bottleneck and nothing else here is measured.** 3.8 MB
  and 200,000 lines through `read() |> trim |> split("\n") |> len` is 0.05
  seconds. What a *parse* of those rows costs in Vine is unmeasured, and it is
  the number the next reading program will care about.
