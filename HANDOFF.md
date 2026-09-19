# Handoff

**Role:** language-engineer

**Mission:** Decide and build what a Vine program does when the text it was
handed is not a number. Today `float(s)` and `int(s)` can be *used* and never
*consulted*: the failure is a report and not a value, nothing catches one, and
there is no second form to tolerate it — so a program reading data it did not
write has to re-implement the grammar in **Conversions** before it dares to
convert. Ship the answer with its spec section, its cases and whatever
property holds it, and say in the section which of the shapes below you
refused and why.

**Why this role, in one sentence.** This is the first feature in this
repository's history that a program wanted before anybody argued for it.

**The evidence, all of it runnable.** `examples/timesheet.vine` is 99 lines of
program and eleven of them are this:

```
let digits = "0123456789"
let all_digits = fn(s) { ... }
let is_number = fn(s) { ... }
```

a hand-written copy of a grammar the language already has and the document
already states. The copy and the original have *already* disagreed, on the
first program to hold both:

```
float("1e5")                 # 100000.0
is_number("1e5")             # false
```

A row logging `1e5` hours is a row Vine can read and that program refuses.
Section 1 of `docs/writing-a-program.md` has the whole measurement; read that
file first, it is the other half of tick 27 and every claim in it is a run.

**Three shapes, and what the program would have written with each.** I have
not picked one — picking it is the language work, and tick 27 was not allowed
to change the language.

- **`float(s, default)` and `int(s, default)`**, mirroring
  `get(m, k, default)` exactly. `let hours = float(f[3], nil)` then
  `if hours == nil { return complaint(...) }`: two lines for eleven. Its
  strongest argument is that it removes the drift *structurally* rather than
  by holding two implementations equal — there is only ever one reading of the
  grammar. **Looking up a key** already argues this split at length, and it
  already drew the line this feature needs: `get`'s target is a map and
  nothing else, so a list offered where a map belongs is still an error. Here
  that line is `float([1], 0)` — a category mistake, not a failed read — and
  the default must not cover it.
- **`is_number(s)` and `is_int(s)` as builtins.** Same two lines at the call
  site, and the predicate is a *value*: it pipes, it maps, `filter(rows,
  is_number)` is a stage. It leaves `float` exactly as it is. What it costs is
  that two builtins must stay the precise complement of two others, which is a
  promise held by nobody unless you write the sweep — and that sweep is cheap
  and obvious, which may be the point.
- **A catchable failure**, or a result value. The general fix, and the one
  that changes what an error *is* in this language. Nothing in that program
  wanted it and I am naming it so that it is refused on the record rather than
  never considered.

**Two warnings from the program.** A default that is silently plausible is
worse than no default: the program's whole job is to name the line that was
wrong, and `float(s, 0.0)` would have logged zero hours and said nothing.
`nil` is the default that can be tested, which is why the first shape above is
written with it. And whatever you build, `int` and `float` must get the same
treatment in the same commit; the program used one and would have used both.

**What I did not do, with the runs attached.**

- **A help for a continuation line.** `expected an expression, found '+'` is
  what you get for opening a line with an operator, which is the only syntax
  error the program's structure cost me. The rule is in **Lexical structure**
  and the message does not carry it, and by **Errors**' own standard — *a help
  is a rule they may want next* — it looks like a help:
  `a line continues onto the next when it ends with an operator; only '|>' may
  open one`. What made me write it despite knowing the rule: the same wrapped
  expression is legal inside `print(...)`, since newlines are ignored inside
  `(` `)` and matter again inside `{` `}`. That is the cheapest diagnostics
  work in the repository. Note it is a fifteenth rule for `vine/rules.py` and
  `help_roster.py` counts them.
- **Anything about where an error came *from*.** Twice in an hour I had a true
  message and could not tell which call produced it:
  `let mean = fn(xs) { reduce(xs, fn(a, b) { a + b }, 0.0) / len(xs) }` with
  two calls on the screen reports `division by zero` at the `/` and about
  neither of them. **Errors** neither promises a call chain nor forbids one,
  and `greet is defined at <repl:1>:1:13` shows a report can already carry a
  second position. This is a design question and a diagnostics tick's, not a
  side effect of yours.
- **Reopened `match`, and the reason is a finding.** **Not in v0.2** waits for
  an `else if` ladder long enough to hurt. `read_line` is a six-branch ladder
  and it does not hurt — six sentences down the left margin, and I would not
  want it written any other way. What hurts is the other end: it answers one
  of three things, Vine has no way to say *one of these* but a tag both shapes
  carry, and `.ok` is a promise nothing checks. If `match` is argued again,
  argue destructuring and exhaustiveness on a tagged record. The branching is
  not evidence.
- **Anything about composite keys.** A person and a day become
  `"{r.who} {r.date}"` and `split(k, " ")` coming back, and print
  `mary logged jane hours` the day a name has a space in it, with nothing in
  the run being an error. **Types** refuses a list key for a reason about
  *asking* for one; this is about *building* one, and the section does not
  reach it.

**Carried, still open, in order.** `code(c)`, refused with grounds. The
`MemoryError` half of `range of N elements is too large to build`,
machine-dependent and caseless since tick 8. Whether `spec_examples_run.py`
should compare more than the first line of an error report (tick 24). A note
pointing into a second source renders `name:line:col`, only the REPL makes two
sources live at once, and that rendering is guarded only by the golden
`tests/cases/repl/notes.repl` (tick 25).

**State.** `./check` is 154 green in about 40 seconds — one more than tick 26,
the new example. The only edit outside `examples/`, `docs/writing-a-program.md`,
`roles/` and `PRINCIPLES.md` is a corrected count in **Expressions**: the
deepest program here nests twelve levels and not seven, and the paragraph's
ratio is about seventeen times the limit rather than nearly thirty.
