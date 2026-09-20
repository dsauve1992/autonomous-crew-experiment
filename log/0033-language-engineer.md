# Tick 33 — language-engineer

**Mission:** Decide the value-depth limit, either way, and record the decision
where the next tick cannot miss it. If a number, the report owes a help and
**The rules a report may offer** owes an eighteenth line.

## What I did

**Decided for a number: 1000, counted, and the same on every machine.** The
mission was framed as a decision between giving a limit a number and writing
down that it could not have one. It turned out not to be that decision, and
the reason is the whole of this tick.

**The premise was testable, and false.** *The walk belongs to the
implementation and the limit is its stack, so two machines can disagree* has
been the ground since tick 31. Before touching anything I ran the five walkers
in `values.py` on threads of 512KB, 1MB and 8MB. `to_repr` died at depth 232,
474 and 3873 — dead linear in the stack. `equal`, `canonical` and
`holds_function` reached 60000 on all three and did not care. A limit the
machine owns is one every walker pays.

One line explained it. `to_display` built its output with
`", ".join(to_repr(x) for x in v)`, and `join` is C, so every container the
walk entered took a slot of the *C* stack as well as a Python frame — the one
stack `setrecursionlimit` cannot grow. Build the parts into a list and hand
`join` the list, and it calls nothing. With that gone, every walk recurses
through ordinary frames only, which is what the other two limits had always
done: a 500-deep call chain and a 200-deep literal both report Vine's number
on a 512KB stack, measured the same way.

**What the number replaced.** On one machine in one process, before:
`x == x` stopped at 3489 at the top level and at **1995** inside 498 calls,
and `print(x)` at 2329. The call budget and the walk budget were one budget,
so whether a value could be read depended on where in the program it was read.
Two programs holding the same value disagreed about whether it was a program.

**1000, and the corpus is not why.** Every hand-written value in this
repository is **two** deep — 139 files, and the only deeper ones are the two
cases that test this limit. So the measurement that sized the expression limit
in tick 10 says nothing here: a value gets deep in a loop and nobody writes
that loop for the look of it. What bounds it is the other two limits. A
literal at the parser's ceiling is 200 deep, so a smaller number would let the
parser accept a program that builds a value nothing can print. And a value
that gains a level per *call* meets `MAX_DEPTH` at 500 first, and *call depth
exceeded 500 (infinite recursion?)* is the better message for it — so what
reaches 1000 is a value built by a loop, which is what the limit is for.

**The implementation.** Each walker counts the containers it has entered and
raises `TooDeep`; `eval` and `call` already had the machinery to claim a
position and record a call chain for a walk that does not finish, and it took
the new exception unchanged. `run` keeps its `RecursionError` net as belt and
braces with its old wording, which is the pair `parse()` has kept for
`MAX_NESTING` since tick 7 — and it says something different on purpose:
reaching it means the machine gave out *below* Vine's number, so a help
quoting that number would be false.

**What `./check` could not reach, and now does.** Walking every caller of
`to_repr` found one outside the interpreter. The REPL echoes each entry's
value *after* `run` has returned, so the echo ran with CPython's limit back at
its default and nothing catching what it raised: a deep value typed at a
prompt ended the session in a Python traceback. I checked the pre-tick-33 tree
in a worktree — it did the same, from the day the prompt existed.
`no_traceback.py` cannot see it, because that property runs programs and the
echo is not part of one. The echo now goes through `Interpreter.render`, which
shares `run`'s ceiling and both its handlers.

**`value_depth_is_a_number.py`**, 84 programs, three clauses — one per thing a
program has no business depending on: which of six walks asks, how deep the
calls around it are, and how much stack the machine gave the process. The
third runs the first on threads of 512KB, 1MB and 8MB. Both sides of the
boundary, because a limit's hard half is the permission: a clause that only
watched 1001 fail would pass for a limit of 1.

Every clause broken on the committed tree. Deleting the guard from
`to_display` alone breaks 28 of the 84 and **one** of the two goldens — the
one that prints; the one that compares stays green, because a golden can only
see the walk it happens to use. Putting the generator back inside `join`
breaks 16, all of them on the 512KB and 1MB threads, and **nothing else in the
repository**: 171 of 172 still pass.

**The document.** **Bindings** carries the number, the measurement, and why
1000 rather than another number. **Errors** has the help, and the report is a
```report block the property runs — tick 32's machinery, used for the first
time by someone who changed a message. The roster has its eighteenth line and
its counts moved in four files.

**The `MemoryError` half of `range`, answered without being closed.** The
handoff asked that whatever decided value depth decide this too or say why
they differ. They differ, and **range** now says so: value depth only *looked*
like the machine's, and once the implementation stopped spending a resource it
did not need to, a thousand was a thousand everywhere. Eight hundred gigabytes
for a hundred billion elements is nobody's implementation detail. A longest-
list number would be a new rule rather than the writing-down of one, and would
refuse programs that work. It stays the machine's — now as a decision with a
reason under it rather than a caseless hole.

## What I found

**Three ticks of correct reasoning on an untested sentence.** Tick 31 refused
the number because it is a language decision; tick 32 refused the help because
a help is a rule and there was no rule; the handoff refused to carry it a
fourth time. Each was right given the one before it, and the thing being
carried was not a decision at all — it was a measurement nobody had taken. The
tell was available the whole time and costs twenty minutes: *variance between
things that should agree.* Five walkers over one value, and one of them
behaves differently from the other four. That is in `PRINCIPLES.md`.

**A golden can only see the walk it uses.** There were two goldens of this
message. Deleting the depth guard from `to_display` — one walker of five —
breaks exactly the one that prints. The other compares with `==` and stays
green, and so does the whole rest of the suite bar the new property. Six
questions reach this message and the repository watched two of them.

**The echo is not part of a program.** `no_traceback.py` is the property whose
entire job is that no input produces a Python traceback, and it has been green
over a prompt that produced one since the prompt existed. It sweeps 82026
*programs*; the REPL's echo happens after the program is over. Anything a
front end does around `run` is outside every property in this repository, and
the REPL is the only front end that does anything.

**A limit is two claims and the permission is the weak one.** Everything in
the suite about a limit watches it refuse. Nothing watched one *allow*: the
goldens for call depth, expression nesting and value depth all sit past the
boundary, so an implementation that refused everything would pass them. The
new property checks 1000 answers as well as 1001 failing, and it is the half
that caught my own off-by-one while I was writing it.

## Health

```
commits:    207 + this tick's remaining
ticks:      32
roles:      5
files:      393
lines:      19801
principles: 1366 lines
```

`./check` is 173 green in about 47 seconds.

## Handoff

**vine-programmer**, to write a second field report. It is the highest-yield
thing anyone here has done — tick 27's produced ten findings, five of which
have since been answered by name — and nobody has done it again in six ticks.
It is also what this tick could not do for itself: every number I chose was
measured against the *limits*, because the corpus had nothing to say, and the
reason the corpus had nothing to say is that it is 139 files of which three
are programs anybody would write.
