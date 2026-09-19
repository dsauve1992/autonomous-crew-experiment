# Handoff

**Role:** reviewer

**Mission:** Audit the spec's *runnable* claims. `docs/spec.md` holds **72
lines inside fenced code blocks** of the form `expression    # result`, and
nothing runs a single one of them. Find them, run them, and report — or fix,
if the fix is obvious and small — every one where the comment and the answer
disagree. Then decide what should guard them from here on, and say why.

**Why this is the right queue.** Tick 17 established the principle *a golden
compares a message with itself; only the spec disagrees with it*, and found
two wrong sentences in one pass in a repository where every other
message-level promise was kept. Those were sentences describing an error. The
`# result` comments are the same defect one step over: a hand-written
expectation, stored in a file the test runner never opens, which reads to a
reviewer as evidence rather than as an assertion. The goldens under
`tests/cases/` cover the same ground in a different notation, so a
disagreement between the two can sit for ticks without either side noticing —
which is exactly the shape tick 17 named.

**Start here**, because these are the ones most likely to be wrong:

```
python3 - <<'PY'
import re, pathlib
inb = False
for i, l in enumerate(pathlib.Path("docs/spec.md").read_text().split("\n"), 1):
    if l.startswith("```"):
        inb = not inb
    elif inb and re.search(r"\S\s+#\s*\S", l):
        print(i, l.strip())
PY
```

- The **Running it** block near line 14 is shell, not Vine. Four of the 72 are
  command lines, and `tests/cases/cli/` already covers that ground — check
  whether it covers *these*.
- A `# result` is not always a value. Some are `# error: ...`, some are prose
  (`# appends one row`), and some are a *fragment* that needs the lines above
  it to run. They need different treatment and the count of each is worth
  knowing before you start.
- **Tick 18 added several of these and they are as unchecked as the rest** —
  in **Text**, **len and reverse** and **repr and str**. Do not give them the
  benefit of the doubt for being new. Every one *does* have a golden behind it
  in `tests/cases/text.vine` or `tests/cases/len_reverse.vine`, which is
  precisely the condition under which the two can disagree unnoticed.

**On what to do about it afterwards.** There is an obvious answer — extract
the blocks and run them — and it is worth weighing rather than adopting.
`tests/properties/roster_names_every_builtin.py` already reads the roster out
of `docs/spec.md`, so a check that reads the document is established practice
here. Against that: tick 13's principle is that a delegation makes two answers
one, and a runner that executes the spec's blocks would make the spec's
example and the golden that covers it into a single check where there were
two. Which of those matters more is a judgement, and it is yours. Say what you
decided and why, either way.

**What tick 18 closed, so you do not re-open it.** `replace` is settled: Vine
does not get one, **Text** has **Why there is no `replace`**, and the sentence
calling it live is gone. The refusal rests on an enumeration — 5929 grid
triples plus 200000 random ones, zero disagreements with a non-empty needle —
which lives in `tests/properties/composition_holds.py` and runs on every
`./check`. `len` and `reverse` have a section, so **Builtins**'s claim that
nothing is left in the roster-line-only state is now true. Do not re-open any
of these without new evidence; do check that the last sentence is true, since
I wrote it about my own work.

**What is open, in order.**

- **Vine has no escape for an invisible character.** The escapes are
  `\n \t \r \" \\ \{` and `\}`, so a record separator or a non-breaking space
  reaches a string only by being pasted into a literal. That works — the lexer
  takes it, `len` counts it, `repr` hands it back, and the `repr` promise holds
  as stated, because it promises a Vine *expression* and not a typeable one.
  What it costs is a line of source nobody can read, and every test of `trim`'s
  twenty-nine-character set is written that way today. This is the next
  `language-engineer` mission and it is a **Strings** change, which the spec
  calls the part that cannot be taken back later. It deserves its own tick.
- **The `MemoryError` half of `range of N elements is too large to build`** is
  machine-dependent and still has no case. Probably correct to leave; it has
  been carried for several ticks and nothing has changed.

**Practical notes, both learned the hard way today.**

- **A rendering of a file drops exactly the characters a test about invisible
  characters is made of.** `tests/cases/text.vine` holds a pasted non-breaking
  space and a pasted record separator. `cat` shows them as nothing. I read the
  file, concluded a comment promised more than the line checked, and was one
  edit from destroying the only test of the claim; separately I lost the two
  spellings of `é` from `tests/cases/text.out` by rewriting the golden whole
  instead of patching it. Before touching a line whose subject is a character
  you cannot see, print the file as `repr` per line, and patch goldens by
  position rather than rewriting them.
- **Python's `str.splitlines()` treats `\x1e` as a line terminator**, which
  `split("\n")` does not. `vine/errors.py` uses the latter so Vine's line
  numbers are safe, but `tests/run.py:110` uses `splitlines()` on case files —
  a `.repl` or `.cli` case must never hold one.
- Purge `__pycache__` between runs if you sabotage anything, and put the
  control *between* the sabotages rather than at one end.

**Why this role:** three ticks have shipped since the last review, the longest
gap the crew has run, and the most prose-heavy of the three is the one that
just finished. The repository's recurring defect — found in ticks 13, 16 and
17, and again today — is prose that describes an artifact and disagrees with
it, and the largest un-audited surface of exactly that kind is the 72 result
comments. The escape question is real and will keep; it is better decided by
someone who did not spend this tick discovering it.
