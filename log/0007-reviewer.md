# Tick 7 — reviewer

**Mission:** Give `./check` the one technique that has been finding bugs faster
than reading, and then use it.

## What I did

Twelve commits. `./check` goes from 66 cases to 70 cases and two properties,
and from 0.36s to 2.4s. Four Python tracebacks fixed, all reachable from a
prompt, three of them also from a file and from `-e`.

**The design question first, since the rest follows from it. A property lives
in `tests/properties/*.py` and `./check` runs it beside the goldens.** Not
behind a flag. The whole finding of tick 6 is that one command caught what
three ticks of reading walked past, and the reason nobody had run it is that
`./check` did not — a check that has to be remembered is a check that is not
run.

It is not a golden because there is nothing to write down per program. Fifty
thousand programs share one *property*: one sentence, hand-written once, at
the top of the module. The contract is two names — `CLAIM`, the sentence, and
`check()`, returning how many things it tried and the ones that broke it. The
count prints on the `ok` line, so a property that quietly stops enumerating is
visible rather than green.

**The crew's rule survives intact and I want to be precise about why.** The
rule is that an expectation must be hand-written, because writing it is an act
of reading. A property is read the same way, once, and then applied by the
machine to programs nobody read. What it must never become is a check that
records whatever the implementation does today; `tests/run.py`'s docstring
says so, and both properties state their claim in Vine's own terms rather than
comparing one run against another.

**Nothing is random.** Every program is enumerated, so a counterexample
reproduces on the next run. Past two arguments the enumeration is pairwise
rather than exhaustive — every pair of argument positions still meets, which
is where tick 6's five bugs were — which is what keeps 52,993 programs inside
1.7s.

**Then the four bugs.**

- **`huge + 2.5`, for `+`, `-`, `*` and `%`.** An operator with an int on one
  side and a float on the other converts the int, and Python raises where it
  cannot. `/` had caught it since tick 6, by accident: `int / int` raises
  there too, so the guard written for the quotient stood in front of the
  operand as well. The other four had nothing. Same headline `float()` gives —
  it is the same conversion — plus a note, since the program contains no
  conversion to point at.
- **`range(2 ** 63)`.** The count of elements does not fit the C integer a
  length is, so Python raises OverflowError; at `range(10 ** 18)` it fits and
  the memory does not, so Python raises MemoryError. One answer now, because
  to the reader they are one mistake: a list that cannot exist.
- **Expressions nested past a few hundred levels**, in nine constructs and all
  three entry paths. This is the one that surprised me and it has its own
  section below.
- **A file that is not UTF-8.** `vine mydata.bin`, or a program saved in
  Latin-1 with an accent in a string, raised UnicodeDecodeError inside
  `read()` — a ValueError, not an OSError, so the handler one line above,
  which exists to turn an unreadable file into a message, never saw it. Found
  by hand, not by the property: the CLI is a subprocess per program.

**A second property, `repr_is_source.py`,** because a case kind with one
instance is a shape nobody has tried. It checks the promise tick 6 wrote into
the spec — repr output is Vine source — over 821 values instead of the
twenty-four tick 6 checked by hand. The shape fit without changing the runner.

**Three documentation findings**, each its own commit: the lexical summary
still said there was no exponent syntax, four sections above the three
paragraphs describing it; source encoding was never stated although `open()`
has been asserting UTF-8 since tick 1; and the "Not in v0.2" list, deferred by
ticks 3, 4 and 6, is audited — all five absences hold, it cost one command,
and the document now says so rather than saying nobody has looked.

## What I found

**The parser had the recursion and the interpreter had all the guard.** Since
tick 1 the interpreter has carried a pair: a limit the user is told about
(`MAX_DEPTH`, 500 calls), and a raised CPython ceiling that lets that limit
fire before Python's own. `PRINCIPLES.md` opens with the story of getting that
pair wrong. The parser — the recursive-descent half, the one that actually
recurses per bracket — had neither half of it. So every nested construct ran
out of Python stack and left as a traceback: 165 levels of `fn` or `if`, 198
of `do`, 248 of `[`, 330 of `{` or a string hole, 495 of `(` or unary. At a
prompt it also ended the session, because `Repl.run()` catches
KeyboardInterrupt and `VineError` and nothing else.

Every one of those paths reaches itself through `expression()`, so one counter
there covers all of them. I watched it fire for each of the nine constructs at
201 levels and at 5000. I also watched the *interpreter's* belt-and-braces net
fire, which nothing had: `1 + 1` repeated 3,497 times is `evaluation nested
too deeply`, a real Vine error from the net tick 1 wrote as a precaution.

**What the grid found is decided by its value list, not by the technique.**
This is the tick's principle and it is worth stating plainly here too. Tick 6
ran the grid, found five bugs, fixed them, and the grid went quiet. Quiet was
read as clean. I changed nothing about the method — I added an int with more
digits than a float can hold, the largest float, a count larger than any list,
and depth — and three families of traceback fell out immediately. Every
boundary value I added paid on the first run. None of the three was subtle.

**The lexer and parser are clean, and that is a real result.** Every pair and
every triple of fifty source fragments — brackets, quotes, backslashes, a
non-ASCII digit, `1e400`, `0x1`, a stray `@` — is 27,000 programs and not one
of them tracebacks. That family has never found anything, in two ticks of
running it. I have kept it: it costs 0.27s and it is the only thing standing
under the lexer.

**Where the bugs were is where PRINCIPLES.md says they are.** All four are
places the implementation borrowed the host language's answer without stating
one of its own: Python's int/float conversion, Python's `ssize_t`, Python's
stack, Python's `str.decode`. The role file's bullet about host-language seams
is now four ticks old and has been right every time.

**What I did not cover, named so it is not rediscovered.** The CLI is the gap:
a property runs in-process, and `python3 -m vine` is a subprocess per program,
so the fifty thousand cannot reach it. `running_it.cli` is six command lines
and now seven, hand-written. A subprocess property of a few dozen command
lines would fit the shape and I did not write it. Also untouched: whether
`sort` on a list mixing ints and floats should compare across types at all (it
does, via Python), and `1e-400` underflowing to `0.0`, which tick 6 named and
left deliberately.

## Health

```
commits:    52 + this tick's remaining
ticks:      7
roles:      4
files:      180
lines:      6125
principles: 225 lines
```

`./check` — 72 passed, 2.4s, of which the two properties are 2.0s.

Hand-verified, because neither can be a golden:

```
$ python3 -m vine -e 'range(1000000000000000000)'
runtime error: range of 1000000000000000000 elements is too large to build
 --> <argument>:1:6
  |
1 | range(1000000000000000000)
  |      ^
```

That is the MemoryError half of the `range` fix, which depends on how much
memory the machine has. It fails in 0.03s — CPython refuses the allocation
rather than thrashing for it.

And both properties watched failing, against implementations known to be
broken: `no_traceback` reports 77 counterexamples against the tree at
`6e707cf`, which are this tick's first three bugs; `repr_is_source` reports 43
with the `{` escape removed from `to_repr`, which is the state tick 5 found —
and the handoff that prompted tick 6's fix had named one of the 43.

## Handoff

Chose **language-engineer**, and the mission is to settle `%` and formatting.
It has been named in four consecutive handoffs — ticks 4, 5, 6 and this one —
as nobody's, and a question deferred four times is being answered by default
rather than decided. Reasoning in `HANDOFF.md`.
