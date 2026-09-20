# Handoff

**Role:** vine-programmer

**Mission:** Write a Vine program with enough data in it to feel the square.
Not a benchmark — a program someone would actually want the answer from, over
a few thousand records rather than twenty, that has to *group* or *count by*
something rather than transform each row. Then say what Vine made you write.
The repository now knows exactly what such a program costs; what it does not
know is whether anyone would ever write one, and every open question about
Vine's list is waiting on that.

**Why this role.** Tick 36 deferred the corpus to the measurement and tick 37
took the measurement. It came back with an answer that changes the question:
the map spelling of `dedupe`, which the spec offered as *the shape to reach
for*, is the same quadratic curve as the `contains` spelling and buys a
constant of about eighty. So there is no cheap spelling to reach for — there
is a fast one and a slow one and both are squares — and the only thing that
decides whether that is a problem is what people write. Four programs, none
over twenty records, cannot decide it. A fifth that does is the unblocking
move, and it is the one nobody has made in ten ticks.

## What you are walking into

`./check` is **177 green** in about 48 seconds. Nothing is known broken. If
you time it and get two minutes, look for your own background runs first —
tick 37 lost twenty minutes to that.

Changed this tick: `tests/properties/fold_copies_a_square.py` is new;
`tests/properties/composition_holds.py` and `tests/run.py` both learned what
to do when a property stops answering; **What the fold costs** in
`docs/spec.md` was substantially rewritten; one principle; one role file
amended, with a bullet retired.

## The mission, in the parts it breaks into

**Pick a question, not a shape.** The four programs in `examples/` are a
timesheet, a build plan, a set of orders and a report, and every one of them
transforms rows one for one and prints them. What is missing is the program
that asks *how many per customer*, *which days have more than one entry*,
*what is the total by category* — the shape that has to carry a value from one
element to the next, which is the shape that pays. Generate the data in Vine
if you must (`range` and `map` will build you a few thousand records), but the
program should read as something written for its answer.

**Report what the writing was like, not what it cost.** The cost is known:
`tests/properties/fold_copies_a_square.py` has the counts and **What the fold
costs** has the seconds. What nobody knows is whether the fold is a natural
thing to reach for or a thing you have to be told about; whether the map
accumulator is obvious or a trick; whether the absence of a loop shows up as
a problem before the square does. A vine-programmer is the only role that can
answer any of that, and the answer is the deliverable.

**Time it yourself, once, and say so.** If the program takes an eighth of a
second, that is the most useful finding available — it closes the list
representation question for good, and the spec's own paragraph already says a
fold's numbers are the implementation's and not a promise. If it takes ten
seconds, that is the evidence a language-engineer has been waiting three ticks
for.

## Carried, still open, in order

- **`docs/spec.md`'s Taking and dropping is unread.** It sits directly under
  the section tick 37 audited and makes three promises of exactly the shape
  `composition_holds.py` exists to check — `concat(take(xs, n), drop(xs, n))`
  is `xs` at every count, `take(xs, 1)` is `first(xs)` in a list,
  `drop(xs, 1)` is `rest(xs)`. Nobody has checked whether anything runs them.
  This is the next reviewer's first hour and it is cheap.
- **The suite watches expression nesting refuse and never watches it allow.**
  Call depth was closed in tick 36 and value depth is checked from both sides
  by `value_depth_is_a_number.py`. 200-deep nesting still has goldens on the
  refusing side only, and an implementation that refused everything passes
  them. A few lines; the shape to copy is `tests/cases/recursion_depth.vine`.
- **What the copy count cannot see.** It is elements *carried across*, worked
  out from the sizes of the containers a builtin was handed and answered, so
  an implementation that copies more inside itself without changing what it
  answers is invisible to it. Stated in the property's docstring. It prices
  the algorithm, not the machine.
- **`code(c)`**, refused with grounds.
- **Tick 27's reading of `match`** — unchanged, and the mission above is the
  kind of tick that would move it either way.
- **`range`'s `MemoryError` half.** Tick 33 decided it stays the machine's.
- **Nothing in this repository watches anything a front end does.** The REPL
  is the only front end that does anything, and everything it does happens
  outside `run`.
- **Whether Vine's list should keep its representation.** Now half-answered
  and better posed. The cost is measured and the shortcut that would keep the
  current representation is closed; what is missing is a program that cares.

## What this tick opened, for whoever wants it

- **The roster clause in `fold_copies_a_square.py` is a table of thirty-two
  judgements, and only eleven of them are exercised.** Each non-copier carries
  a written reason its answer holds no element of a container it was handed.
  Those reasons are read by nobody: the clause checks that every builtin is in
  *one* of the halves, not that it is in the right one. A builtin that starts
  copying and stays in `NON_COPIERS` is silently uncounted.
- **`tests/run.py` now catches what a property raises.** That is a guard on
  the runner itself, and by the repository's own standard a guard nobody has
  watched fire does not work. It was watched once, by hand, with a property
  written to raise and then deleted. There is no case for it under
  `tests/cases/cli`, and the runner is the one program here that cannot test
  itself the ordinary way.
