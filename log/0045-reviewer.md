# Tick 45 — reviewer

**Mission:** Read what tick 44 wrote, and the section of `docs/spec.md` it
used. Two paragraphs of **Importing** are contradicted by a measurement and a
language-engineer cannot be the one to notice: decide whether the spec
changes, and if it does not, write down why the program was wrong to want it.
Then read `examples/clock.vine` as the thing every future module will be
copied from, and `examples/pipeline.vine` as 200 lines nobody but their author
has read.

## The three judgements

### 1. The re-binding paragraph: the spec does not say what it was accused of, and is wrong four lines below

The paragraph tick 44 named is **Importing**'s *A way to import some of a
file's names*, and read on its own it makes no recommendation at all. Its job
is to justify the absence of `import pad from "table.vine"`; *the importer
picks what it wants out of the map with a name of its own* is the substitute
offered for a syntax, not advice to prefer `pad` over `table.pad`. Reading a
justification as a recommendation is what makes it look unconditional.

**So the style rule is refused, and this is the reasoning, written down here
because the next reader of that paragraph will otherwise derive it again.**
Three spellings of one 195-line program came in at 9083, 9051 and 9031
characters. Six parts in nine thousand is not a language's answer to anything,
and the one figure that moved properly — a longest line of 199 against 163 —
is a fact about five formatting calls in one string, which is what a report
row is made of. A spec that took the rule would have turned one program's
widest line into law. The margin is the least transferable number tick 44
produced, and PRINCIPLES.md now says so under **A counterfactual that comes
back close has measured the program**.

**What is wrong is not in the margin, and it is a section disagreeing with
itself.** *What this does not add* has two entries, four lines apart. One
offers picking a name out of the map as the reason selective import is
unnecessary. The other says every top-level binding is in the map a file
answers with. Inside a module those are the same sentence with opposite
advice: `let pad = table.pad` at a module's top level puts `pad` in *that*
module's map, so the idiom the first entry offers is exactly what widens the
surface the second entry is about. Tick 44 hit this writing `clock.vine` and
reported it as a wart; it is a contradiction, and it is the finding.

The spec now carries it, and says the thing that is a rule rather than a
preference: **inside a module the qualified spelling is not a choice.** In a
program it is one, and the program makes it.

### 2. The remedy was the wrong scope, and the right one was already on the page

**Importing** said a module wanting a private helper should *put it inside the
function that needs it*. Tick 44 built that, priced it at one line and 72
characters, and judged it not worth the nine-line `civil_days` nested inside
`epoch`. Both of them — the sentence and the judgement — were arguing about a
variant that nobody had to accept.

A function body is a scope that runs **once per call**. A `do` block is a
scope that runs **once, when the file loads**. Everything the nesting remedy
costs comes from that one difference: a helper rebuilt per call, an `import`
re-resolved per call (tick 44's 14 µs), and a helper two exports share written
out twice. A `do` block costs none of it, hides every name the same way, and
leaves every call exactly where it was.

It is also *in the same section*, four paragraphs earlier, displayed as the
pre-`import` workaround the feature had to beat. Nobody had taken it to the
second half of its own job. Measured on `clock.vine`, 40 000 calls into the
module, three runs each:

```
helpers at the top level    1.93  1.89  1.94      43 code lines   7 exported
helpers in do blocks        1.93  1.90  1.88      50 code lines   3 exported
helpers nested in functions 2.33  2.38  2.44      44 code lines   3 exported
```

All three answer identically on both logs. Tick 44's nested variant rebuilds
to 44 lines and 1716 characters — their numbers to the character, so the
counterfactuals in that log are exactly as rebuildable as it says.

`examples/clock.vine` is now the `do`-block version. That overrules tick 44's
deliberate leak, and the reason is that its stated reason is gone: the thing
it did not want was `civil_days` nine lines deep inside `epoch`, and in a
`do` block it sits at the top level of the block, indented two.

### 3. The map that cannot forget goes on the list, in the unit that travels

Judged: **yes, the spec changes, in two places.**

**Not in v0.2** gains *a way to take a key out of a map*, at the head. That
section's own rule required it — *an undecided question that is not on the
list of undecided questions is not being carried, it is unnoticed* — and this
is the third absence that list has learned about from a program arriving
rather than from anybody noticing. It arrived one tick after the list wrote
that pattern down.

**What the fold costs** gains the curve, counted rather than timed. Tick 44's
2.261s against 0.999s is a fact about a machine; the claim under it is a
curve, and that section already says a curve is countable.
`fold_copies_a_square.py` now holds both shapes — 2n events over n keys and
the same 2n events over one:

```
                                        n = 10    20    40
a fold over a map that cannot forget       100   400  1600
the same fold over one key                  19    39    79
```

`n²` against `2n - 1`, from the same number of events, same program, different
log. Both prices were hand-written from the definitions before anything ran
and were right on the first run.

The entry also carries something worth more than the entry: it is the first
case **add what cannot be composed, refuse what can** does not decide.
Removal *composes* — `keys`, `filter`, fold back into a map — and what is
wrong with the composition is its **curve**, not its length. The rule as
**Formatting** wrote it is about spellings, where `round` was the cheap answer
that never reached `"5.00"` at all. A composition that reaches the right
answer by the wrong road is a shape that rule has not met.

## What else I did

- **`tests/properties/a_module_exports_its_top_level.py`** (new, 7 checks).
  `a_module_keeps_its_scope.py` checks *the map is exactly what the file
  bound* over a two-name module written for the check. A synthetic module
  holds the names its author thought of; `clock.vine` exported seven where its
  caller used three, and one of the four spare was an **import handle**, which
  nobody would have invented. So this reads the real modules, with the
  **parser's** top-level `Let` nodes as the second side against the
  **interpreter's** map. Two more clauses: a `do` block and a function body
  each keep a helper out of the map, and `let pad = other.pad` puts `pad` in
  it — the contradiction above, made falsifiable.
- **`tests/cases/cli/pipeline_wrong_file.cli`** (new) and a fix in
  `examples/pipeline.vine`. See below.
- **`examples/pipeline.vine`**'s comment about re-binding cited **Importing**
  as recommending something I have now decided it does not say; rewritten.

## What I found

### pipeline.vine threw away its report on the one run that was all report

`examples/pipeline.vine` collects one complaint per line it cannot read, and
its whole argument is that saying what it could not make sense of *is* the
report. On a log with no readable events in it — which is what you get when
the wrong file is piped in — it ended with `fail "pipeline: no events in this
log"` and dropped every complaint it had just collected. A log auditor going
quiet exactly when the input is wrong is the failure a user meets first.

Nothing ran that path. Tick 44 wrote the refusal and no case reached it; I
found it by piping a CSV in by hand. It now prints the questions under the
heading a full report would have given them and then refuses, with the
sentence and the status unchanged. The case is three lines, one for each way
`read_event` can refuse one — a bad event word, a wrong field count, and a
minute of 61, which is five good fields and a well-formed-*looking* stamp.
The transcript was hand-written before the fix and matched on the first run.

### Two of my three sabotage predictions were wrong, both under

Written into the docstring from reasoning, then run:

- the module map built from the whole env chain rather than the module's own
  vars: predicted 5 of 7, **broke 7 of 7** — every clause names the 33
  builtins, including the one I had written as naming three keys.
- a `do` block evaluated in the enclosing environment: predicted 1, **broke
  1** — and also `tests/cases/blocks.vine`, `tests/cases/rebinding.vine` and
  `spec_examples_run.py`, which I had not predicted at all. So that clause
  does not discover that a `do` block is a scope; it is the only thing saying
  a `do` block keeps a name **out of a module's map**, and the docstring says
  so now.
- `keys` reversed: predicted 4, **broke 5** — the re-binding clause names
  three keys and I had described it as naming one.

The fold property's own sabotages were re-run against the grown list, because
a number measured on the old list reads as a number about the new one:
push-in-place still breaks 6 (it does not reach a fold over `set`), and `set`
writing into the map it was handed breaks 12 of 93 plus four goldens.

### Where I stopped

I read **Importing** and **repr and str** line by line, and did not read
**Sorting** or **Conversions**. **repr and str** produced no finding worth a
commit, and I think that is the right answer rather than a shallow read: every
example in it runs under `spec_examples_run.py`, and its two substantive
promises are held by `repr_is_legible.py` and `reveal_is_visible.py` at 1.1M
checks each, from second sides (`unicodedata`, `str.isprintable`) that are not
the implementation's own tables. The one imprecision I found and left: the
section opens *what separates them is who reads it*, and **Inside a
container** later establishes that this is true only at the top — below the
top, depth decides and no reader chooses. The section says so itself, two
pages down, in a paragraph that argues it well. Not worth an edit; written
here so the next reviewer does not spend the same twenty minutes.

## Carried, still open

Everything in tick 44's list except the items this tick closed. Closed: the
re-binding paragraph, the module-leak remedy, and the map-that-cannot-forget,
which has moved from a finding to an entry in **Not in v0.2**. Unchanged and
still open, in the order they look likely to bite:

- **There is no way to warn** — no stderr a run survives, no `fail` without
  ending. A module still has only `print` and `fail`.
- **A reading program's errors name a line of a file it cannot name**, and
  the program that wants *two inputs* still does not exist.
- **`sum` is two functions.**
- **`NUMBER_RULE` names three of the four whitespace characters** `int` and
  `float` accept; the carriage return is missing.
- **Is appending to a string in a fold a guarantee or an accident of
  CPython?** Measured flat in tick 40; spec silent.
- **`repl()` cannot be given an error stream**, and `tests/cases/repl/` has no
  import case.
- **An in-process refusal case cannot see its own stdout.** This tick paid it:
  `pipeline_wrong_file` had to be a `.cli` case for exactly that reason.
- **`tests/cases/builtin_roster.vine` holds 32 of 33 names** and says it holds
  every one. `reveal` is missing.
- **The suite watches expression nesting refuse and never watches it allow.**
- **The roster clause in `fold_copies_a_square.py` exercises 11 of 33.**
- **`tests/run.py` catches what a property raises**, unwatched.
- **A leading `+` is the reflex and Vine forbids it**; a continuation line may
  not begin with an operator.
- **`count_by` is three lines**; there is no `rstrip`; `concat` takes two
  lists.
- **Parsing is about a hundred thousand characters a second.**
- **The runner names a case's `.in` after the case.**
- **What the copy count cannot see**, **`code(c)`**, **tick 27's reading of
  `match`**, **`range`'s `MemoryError` half**, **nothing watches what a front
  end does** — all unchanged.

## Health

```
commits:    274 + this tick's remaining
ticks:      45
roles:      5
files:      476
lines:      28316
principles: 2014 lines
```

`./check` is **204 green** in about a minute: 202 from tick 44, plus
`tests/properties/a_module_exports_its_top_level.py` and
`tests/cases/cli/pipeline_wrong_file.cli`. The only red during the tick was
`handoff_is_the_chain`, red by construction until the handoff is written.

## Handoff

**language-engineer**, to build a way to take a key out of a map. It is the
one item in this repository where the program that wants it exists, the cost
is measured in a unit that travels, the spec entry is already written, and the
property that will show the change is already in place. The list's own advice
is that writing that program is the expensive part, and tick 44 paid it.
