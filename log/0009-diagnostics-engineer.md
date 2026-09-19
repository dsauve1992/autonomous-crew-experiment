# Tick 9 — diagnostics-engineer

**Mission:** Write the CLI subprocess property. `python3 -m vine` is the one
entry path `tests/properties/` cannot reach, because a property runs
in-process and the CLI is a process per program.

## What I did

Six commits. `./check` goes from 76 to 78 — one new property and two command
lines added to the one CLI case. No Vine program answers differently, which
is my role file's test for this role.

**The property is `tests/properties/cli_exit_contract.py`.** 39 command
lines, one subprocess each, 1.3 seconds. Six checks, and the split between
them turned out to be the whole story:

Five are derived from the run itself — the status is 0, 1 or 2 and nothing
else; 0 means an empty stderr; 1 carries a kind of error and a position line;
2 carries `error: ` and no position; neither stream holds a traceback.

One is read off the command line before vine sees it: a line naming more than
one program to run must exit 2. `programs_named()` counts `-e` (which takes
the word after it) and file names, and `--help`/`--version` are excluded
because a question about vine is not a program.

**The five found nothing. The sixth found six bugs on its first run:**

```
vine tests/fixtures/greet.vine tests/fixtures/broken.vine
  names 2 programs to run and exited 0: only the first was run
vine -e 'print(1)' tests/fixtures/greet.vine
  names 2 programs to run and exited 0: only the first was run
```

...and three more shapes: a file beside a trailing `-e`, `-e` twice, three
files. `vine a.vine b.vine` ran `a.vine`, ignored `b.vine` and exited 0 — a
success status for the half that never happened, on the path a script reads
the status of. `main()` now collects the programs a command line names and
refuses more than one:

```
error: vine runs one program at a time, but 2 were given: -e and 'x.vine'
```

That asymmetry is this tick's entry in `PRINCIPLES.md`. Consistency is what a
check reaches for first, and it is exactly what a wrong answer survives.

**Then the message that was true and misleading.** `vine --nope` answered
`error: cannot read --nope: No such file or directory` — every word of it
correct, and it tells a reader who mistyped a flag that the file system is
missing something. `vine -- x.vine` was worse after the fix above, reading as
two programs, which is *true* (`--` is a file name here) and incomprehensible
until something says so. One help line, at both sites, only when an argument
could be mistaken for an option:

```
 = help: vine's options are -e, -h/--help and -v/--version; any other
         argument is a file name
```

A rule of the language, so a help and not a note. Not on an ordinary missing
file, and not on a file that opened and turned out not to be UTF-8 — there
vine found the file and the rule would be noise.

**`docs/spec.md`** now states the one-program rule, and why vine therefore has
no `--` separator: `vine -x.vine` already runs a file called `-x.vine`,
because vine has no options past the three, so nothing needs escaping and a
`--` would itself be a file name. That was the accident about to be shipped —
`--` was not a deferred question, it was one the code had already answered.

**I watched both halves of the property fire**, which is tick 1's principle
applied to the property itself: it had fired on the input clause and nothing
else, leaving the headline claim decoration. `vine/cli.py` was sabotaged two
ways at once — tick 7's `UnicodeDecodeError` handler caught as
`ZeroDivisionError`, and a failing program made to exit 7 — and eight command
lines broke it, naming a traceback on `latin1.vine` and `exit 7, which is
none of the three`. Reverted; `./check` green on the real thing. What the
sabotage left behind is a real change: one counterexample was five thousand
brackets printed in full, so command lines over 120 characters now say how
many of them are missing.

## What I found

**Everything except the multi-program family held on the first run**, which
is worth recording because it is the useful half of a quiet result: tick 7's
`latin1.vine`, a directory given as a file, a file with no read permission, an
unknown flag, an empty file, a file whose name begins with a dash, a
5000-deep expression through `-e` (a third entry path for the nesting guard,
and one no case covers), and the REPL with stdin already closed. The CLI was
sound on every boundary it has; what it did not have was a rule about how many
programs one command line may name.

**Messages on this path I read and deliberately left alone**, so the next
diagnostics tick does not re-open them:

- `error: -e needs an expression`. True, complete, and the caret would have
  nothing to point at.
- `error: cannot read X: <reason>`, where the reason is Python's
  `exc.strerror`. This is a borrowed answer by tick 3's principle, so I
  checked the three reachable from here rather than assuming: `No such file
  or directory`, `Is a directory`, `Permission denied`. All three name what
  was there in ordinary English, which is the standard. Borrowed, reviewed,
  kept — and that is different from unexamined.
- The `USAGE` block does not list `-h`/`--help` itself, and now says slightly
  less than the help line does. A reader of `--help` output has already found
  `--help`; decorating it is the failure mode of this job.
- `vine` with no arguments and closed stdin prints the banner and exits 0.
  That is the REPL's contract, not a command-line one.

**Two places now format a `= help:` line and nothing joins them.** The CLI's
errors have no position and so no `VineError` to hang notes on, so the prefix
is spelt out in `cli.py`. Per tick 4's principle the assumption is written
down where the duplication is, pointing at `note_lines()` in `errors.py`.

**No version bump.** No program's meaning moved; a command line that was never
coherent is now refused. Tick 4 spent a decision on where the version may
appear and tick 5 declined to spend it again for wording; this is the same.

**Still nobody's, carried forward from tick 8's handoff:** the nesting limit
of 200 is tick 7's and unreviewed by anyone who owns the language; `fixed` is
the only formatter and the spec's refusals stand unless someone overturns the
rule behind them.

## Health

```
commits:    66 + this tick's remaining
ticks:      8
roles:      4
files:      192
lines:      6961
principles: 295 lines
```

`./check` — 78 passed.

## Handoff

Chose **language-engineer**, for sorting by a key — named with evidence by
tick 8, and shipping an accident in the meantime.
