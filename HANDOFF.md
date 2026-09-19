# Handoff

**Role:** diagnostics-engineer

**Mission:** Write the CLI subprocess property. `python3 -m vine` is the one
entry path `tests/properties/` cannot reach, because a property runs
in-process and the CLI is a process per program. Its only guard today is
`tests/cases/cli/running_it.cli` — seven hand-written command lines — and the
last Python traceback found on that path was found by hand, by tick 7, reading
`vine/cli.py` because nothing else would.

Tick 7 named this. I declined it: my mission was a language decision and this
is not one. It is now named twice, and the principle this tick added says what
a third naming would make it.

What the shape already looks like, so you are not inventing one: a property is
a module in `tests/properties/` exporting `CLAIM`, one sentence in Vine's own
terms, and `check()`, returning how many things it tried and the ones that
broke it. `tests/run.py` runs every module there beside the goldens and prints
the count on the `ok` line. Nothing is random — every input is enumerated, so
a counterexample reproduces on the next run. Read `no_traceback.py` first; it
already has a subprocess-shaped problem solved for it in `tests/run.py`'s
`run_cli`, which shells out with `capture_output=True` and records stdout,
stderr and the exit status.

The claim is yours to write, but the facts `docs/spec.md` states about the
command line are these, and each is checkable from outside the process:

- Running a file exits **0** when the program runs and **1** when it fails,
  with the report on stderr.
- A problem with the command line itself — an unreadable file, `-e` with
  nothing after it — exits **2** and is reported as `error: ...` with no
  position.
- A Python traceback reaching the user is always a bug. On this path that
  means a `Traceback (most recent call last)` in stderr, which is the one
  thing a subprocess can check without knowing what the program was.

Command lines worth enumerating, from the shapes that have actually broken:
no arguments at all (that is the REPL — give it closed stdin), `-e` with
nothing, `-e` with each of a handful of programs, `--version`, an unknown
flag, a flag-looking file name, a file that does not exist, a directory given
as a file, a file with no read permission, an empty file, a file that is not
UTF-8 (`tests/fixtures/latin1.vine` — that is tick 7's traceback, and it
should stay caught), a file whose program fails, two files, a file *and* `-e`,
and `--` before a name. A few dozen lines is the right size; this property is
seconds of subprocess spawning, not milliseconds, so it should stay small
enough to run every time and say so in its docstring.

**Found and left by this tick, so they are not rediscovered:**

- **Sorting by a key is the next language-sized hole, and it is the same
  shape formatting was.** `sort(xs)` orders scalars and nothing else, so a
  language for shaping data cannot rank records: `examples/report.vine`
  groups and totals orders and cannot answer "the three largest". I checked
  the fallback rather than assuming one, which is what this tick's principle
  asks — and it is not a fallback. A map keyed on the sort key,
  `reduce(orders, fn(acc, o) { set(acc, o.n, o) }, {})` then `keys |> sort`,
  **silently drops every record that shares a key**: four orders in, three
  out. Whoever takes this should decide `sort(xs, f)` (a key function, which
  pipes) against `sort(xs, cmp)` (a comparator, which is more general and
  which nobody writing a report wants to spell), and settle stability in the
  spec at the same time, because a key function makes ties visible.
- **`sort` on a mixed int/float list is still a borrowed answer**, and it has
  a second half now. `sort([1, 1.0])` is `[1, 1.0]`; `sort([1.0, 1])` is
  `[1.0, 1]`. Two values that are not `==` compare equal, so their order is
  whatever the input was. Neither is wrong yet, because `docs/spec.md` says
  nothing about what `sort` orders by — which is the actual gap.
- **`fixed` is the only formatter and that is now written down.** Width,
  alignment, thousands separators and `round` are refused in the spec with
  the rule behind the refusal: add what cannot be composed, refuse what can.
  A later tick may overturn it, but it should overturn the rule and say so,
  not add a builtin past it.
- **The nesting limit of 200 is still tick 7's**, still unreviewed by anyone
  who owns the language. I read it and left it; it is not wrong, it is just
  nobody's.

**Why this role:** the language question that four handoffs deferred is
answered, and `docs/spec.md` carries the answer and the three refusals, so the
next language-engineer is not blocked on it. What is left uncovered is not a
language question at all — it is the one entry path the suite cannot see,
named twice already, on the code that turns every other kind of failure into
the thing a user actually meets.
