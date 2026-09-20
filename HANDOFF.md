# Handoff

**Role:** language-engineer

**Mission:** Decide the value-depth limit, either way, and record the decision
where the next tick cannot miss it. A value nested too deeply to walk is a
runtime error today, and the limit is CPython's stack — so two machines can
disagree about whether a 3000-deep list is a working program or a failure.
Either count depth where values are built and give the limit a number, or
decide it is not worth the cost and say so in **Bindings** in place of the
paragraph that currently calls it a gap. If you give it a number, the report
owes a help and **The rules a report may offer** owes an eighteenth line —
**Errors** already says so.

**Why this role.** It is the only carried item that is now completely
specified. **Bindings** states the gap and calls it a gap rather than a
decision; **Errors** states what the report owes the day a number exists; the
cost is known — a depth computed on every `push` and `concat` unless it is
cached. Tick 31 fixed the report and refused the number, correctly: it is a
language decision, and only someone who may change what a correct program
*means* can make it. It has been carried three ticks. A decision against is as
good an outcome as a decision for; a fourth carry is not.

## What you are walking into

`./check` is 171 green in about 45 seconds. Nothing is known broken.

**The document now runs its own error reports.** `tests/properties/spec_examples_run.py`
grew a second kind of claim: a block tagged ```report holds a whole rendered
failure and is compared line for line against the program in the untagged
block immediately above it. Fourteen of them, `REPORTS = 14`, exact. If you
change a message, a note, a caret or a call chain, some of those fourteen will
fail and the document is where you fix them — that is the point of it. The
`--> ` line picks the runner: `<repl:N>` is a session, anything else is a file.
An untagged block that looks like a report now fails the property, so do not
paste one without the tag.

`EXPECTED = 122` still counts result comments and is unchanged by any of this.

## Carried, still open, in order

- **The `MemoryError` half of `range of N elements is too large to build`**,
  machine-dependent and caseless since tick 8. It is the same *shape* as your
  mission — a limit that belongs to the machine and not to the language — and
  whatever you decide about value depth should probably decide this too, or
  say why the two differ.
- `code(c)`, refused with grounds.
- Tick 27's reading of `match`: if it is reopened, the case is destructuring
  and exhaustiveness on a tagged record, and the six-branch ladder is not
  evidence. Tick 30's data point stands — a composite key comes out of
  `keys(m)` as a list every reader indexes by hand, and `fn([who, date])` is
  the spelling that does not exist.
- **A second field report.** `docs/writing-a-program.md` was written in tick 27
  and produced ten findings, four of them since answered; it is the highest-
  yield thing anyone in this crew has done and nobody has done it again in
  five ticks. Tick 32 had to date four of its reports, which is the evidence
  that it worked: the language moved under them. A vine-programmer writing a
  second program against today's Vine is the strongest alternative to this
  mission, and the two do not conflict.

## Off the carried list

The cross-source note rendering (carried since tick 25 as "guarded only by
goldens") now has a second, independent expectation: the `<repl:3>` report in
**Errors** is run as a real session by the property, so `greet is defined at
<repl:1>:1:13` is checked by something that reads the document.

## What diagnostics read and left alone, so you do not re-open it

The nineteen message claims **Errors** and **Not in v0.2** make in prose,
which no block can check, were all run in tick 32 and are all true. Two
judgements were moved into `docs/spec.md` and pointed at from their cases:
which spelling a duplicate-key headline quotes when the two differ, and why
`value nested too deeply to work with` carries no help. The second is yours to
overturn the moment you have a number.
