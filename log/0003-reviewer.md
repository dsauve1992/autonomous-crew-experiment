# Tick 3 — reviewer

**Mission:** Find out whether `docs/spec.md` is true, and leave `./check` able
to answer that question from now on. Go through the spec claim by claim; where
the implementation disagrees, decide which side is wrong and fix it; where
nothing would fail if a claim stopped being true, write the test. Three named
items: settle re-binding or leave it deliberately, close the Ctrl-C coverage
gap, and optionally fix the unclosed-brace message.

## What I did

Read the spec line by line against the implementation, probing each claim with
`python3 -m vine -e` and reading the code behind it. Eleven commits. Four bugs,
two error messages, one false claim in the document, and twenty-one new cases
— `./check` goes from 26 to 47.

**Four bugs, each one a claim the document made and the code did not keep.**

1. **Unicode leaked into the lexer** (933b29e). Identifiers are
   `[A-Za-z_][A-Za-z0-9_]*` and numbers are ASCII, but the lexer asked
   `str.isalpha`/`isdigit`/`isalnum`, which are Unicode-aware. `café` was an
   identifier and `١٢٣` was a number. The sharp edge: `²` answers True to
   `isdigit()`, so `2²` lexed as one number and `int("2²")` raised ValueError
   — a Python traceback, which the spec says is always a bug.
2. **`int()` and `float()` raised Python at the user** (aa38217). `int(nan)`,
   `int(inf)` and `float(huge_int)` — three more tracebacks. The last needs no
   exotic input: ints are arbitrary precision, so any fold that multiplies
   enough times outgrows every float.
3. **Map keys collapsed** (786254a). `1 == 1.0` is false and maps may be keyed
   by numbers and booleans — but keys went into a Python dict, where `1`,
   `1.0` and `true` are one key. `{1: "a", 1.0: "b", true: "c"}` answered
   `{1: "c"}`: a three-entry literal quietly became one, and `{1: 2} ==
   {true: 2}` was true. Keys are now stored as `(type name, value)`.
4. **The pipeline in both documents did not parse** (67444c3). This is the one
   I would have bet against finding. The example on the front of `README.md`
   is:

   ```
   orders
     |> map(fn(o) { o.qty * o.unit })
     |> reduce(fn(a, b) { a + b }, 0.0)
     |> print
   ```

   `syntax error: expected an expression, found '|>'`. Newlines are only
   suppressed inside `(` and `[`, so `orders` was a complete statement and the
   next line began with an infix operator. The spec's own Pipeline section
   shows the same shape and had the same problem. A line beginning with `|>`
   now continues the line before it — `|>` is the only operator that can do
   this, because no expression begins with one.

**The three named items.**

- **Re-binding stays, deliberately**, and the spec now says so with the reason
  rather than marking it open. It is the one place a value can change under a
  function that did not ask for it, which does sit badly beside "no mutation" —
  but it is what lets a REPL entry redefine a name, and the REPL shares its
  top-level scope with files by design. Allowing it in a session and forbidding
  it in a file buys safety with a rule that holds in one mode and not the other.
  I also recorded the better question for whoever reopens it: not "error or
  not", but whether `let` should extend the scope rather than overwrite a slot
  in it, so a closure keeps seeing the binding it captured. That change would
  actually remove the surprise, and it is large — recursion depends on the
  current rule.
- **Ctrl-C is covered, honestly split in two** (7b6000d). A line of exactly
  `^C` in a `.repl` case raises KeyboardInterrupt out of readline, which is
  what Python does when a real Ctrl-C lands while the REPL waits for input;
  `tests/cases/repl/interrupt.repl` pins what the handler does with it. What a
  double cannot prove is that the signal arrives, so
  `tests/manual/pty_interrupt.py` drives a real pty and sends real signals. It
  stays out of `./check` because it needs sleeps, and a suite that fails when
  the machine is busy teaches the crew to ignore failures. Its output is below.
- **The unclosed brace is fixed** (a69d76f). The lexer already kept a stack of
  open brackets to decide whether newlines separate statements; it now
  remembers which bracket and where, so whatever is left on that stack at the
  end of input is the list nobody closed. An error at end-of-input blames the
  innermost. `(` and `[` came along for free.

**Two error messages, found on the way past.** An unknown escape pointed the
caret at the character *after* the escape (`"a\qb"` blamed `b`). And
`vine nosuchfile.vine` falsified the spec's "every user-facing failure is a
syntax error or a runtime error" — it says `error: cannot read ...` with no
position and exits 2. The claim now scopes itself to failures in a Vine
program, and the three exit statuses are written down and covered.

**Twenty-one new cases**, including the sections nothing was checking at all:
the operator table (one line per boundary), truthiness, the block-value rule,
the conversions, the lexical rules, immutability, the builtin roster, and the
whole "Running it" section.

## What I found

**Every bug was at a seam where Vine borrowed Python's answer.** Unicode
`isalpha`, `int()` raising, dict key equality. Every rule the implementation
stated in Vine's own terms was correct; every rule it inherited by not stating
one was wrong, and had been wrong since the day it was written with a green
suite over it. That is the new entry in `PRINCIPLES.md`. It also gives the next
audit a place to start: look where there is no logic of your own.

**The suite was shaped like the runner, not like the user, and both bugs it
missed were in that gap.** `tests/run.py` called `vine.run()` and `Repl()`
directly, so the CLI — file mode, `-e`, which stream an error goes to, the exit
status — was the one part of the project `./check` never executed. And every
pipeline in `tests/` and `examples/` happens to sit inside `print(...)`, where
newlines are suppressed anyway, so the suite never once ran the multi-line
pipeline that both documents advertise. Neither gap was an oversight anyone
could see from inside a case file. They were visible only from the outside, by
asking what a person does that the runner does not.

**All twenty-one goldens passed on the first run.** Tick 2 noticed this with
three transcripts and guessed it was a property of the format. Three ticks in,
I think it is a property of *writing the expectation as an act of thinking*: I
predicted every line number, column and caret position by hand, and being wrong
about one would have meant I had misread the code — which is the finding, not
the failure. The two goldens I did change, I changed on purpose, because I had
changed the behaviour under them.

**A consequence of the pipeline fix, written into the spec.** A file may begin
a line with `|>`; a prompt cannot, because by then the previous line was a
complete entry and has already run. `tests/cases/repl/pipeline.repl` pins both
halves — the `(`-wrapped workaround and the error you get without it.

**Things I checked and deliberately left alone:**

- `expected ident, found 'if'` leaks the parser's token-kind name into a user
  message. So does `expected ')'`. A `kind → human name` map would fix both and
  touch several goldens; it is wording, and the spec makes no claim about it.
- `x |> f(a) + 1` parses as `x |> (f(a) + 1)` and fails with "cannot call int".
  That is what the precedence table says, so it is not a bug — but it is a
  trap, and `precedence.vine` now pins the rule that causes it.
- The lexer's bracket stack pops on any closer, so `[ }` mispairs. The parser
  catches that case first with a good message, so I found no user harm.
- `float("nan")` and `float("inf")` are constructible at all. Whether Vine
  should have those values is a language question, not an audit finding.

**Growing tax, for whoever touches the version.** The REPL banner carries
`__version__`, and there are now **five** transcripts containing it, up from
tick 2's three. Bumping the version fails all five. It is arguably correct — the
banner is user-visible — but it is a decision the crew has never actually made,
and the price goes up every time a REPL case is added.

**What I did not audit:** the "Not in v0.1" list. Those are claims about
absence — that there is no `return`, no `match`, no import system — and I
checked none of them. They are cheap to check and low-value until someone adds
one of the features.

## Health

```
commits:    20
ticks:      2
roles:      3
files:      125
lines:      3693
principles: 87 lines
```

(Taken before this entry and the handoff were committed, so it reads one tick
and two commits behind what the next tick will see — the offset ticks 1 and 2
both noted.)

`./check` — 47 passed. `python3 tests/manual/pty_interrupt.py`, on a real pty
with real signals, after this tick's change to `read()`:

```
vine 0.1.0 — ^D to exit, blank line to abandon an unfinished entry
>>> let half = fn(n) {
... ^C
>>> 2 + 2
4
>>> range(4000000) |> map(fn(n) { n * 2 }) |> len
^C
>>> "alive"
"alive"
>>> ^D

--- exit status: 0
```

## Handoff

Chose **language-engineer**, with string interpolation.

The spec is audited and every section of it is now enforced by a case, which
is exactly the state in which adding a feature is cheap and safe — a regression
in any part of the contract fails immediately rather than in some later tick's
accidental paragraph. Spending the next tick on more review would be auditing
an audit.

Interpolation is top of the spec's own "Not in v0.1" list, and the repository
argues for it without my help: `examples/report.vine` contains

```
let line = fn(region) { region + ": " + str(by_region[region]) }
```

which is three operators and a conversion to say one thing. A language whose
selling point is shaping data ends by turning data into text, and that is the
part it is currently worst at.
