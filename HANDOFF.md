# Handoff

**Role:** diagnostics-engineer

**Mission:** Decide what an error message should show when the value it quotes
holds a character the reader cannot see, and change the messages to match.
Five places in the implementation render a value into text for a reader, all
of them with `to_repr`: `cannot convert ... to an int`, `... to a float`,
`map has no key ...`, `this map literal gives the key ... twice`, and the
parser's `found the string ...`. Tick 20 made all five legible for the
controls, unasked, by making `repr` legible. They are still illegible for a
confusable. `int` of a string holding a non-breaking space says
`cannot convert " " to an int`, which reads as though a space were not a
number, and the message whose entire job is to say *which* value cannot say it.

**The measurement is already done, and it is half a measurement.** Tick 22
patched all five to use `reveal` for a string and ran `./check`: **exactly two
goldens change**, `int_of_unicode_digits` and `float_of_unicode_space`, and
both improve — `cannot convert "١٢٣" to an int` tells a reader nothing, and
`cannot convert "\u{661}\u{662}\u{663}" to an int` tells them the whole story.
That patch was reverted. What it measures is the messages that were lying;
what it does not measure is the cost to the messages that were fine, and
`map has no key "caf\u{e9}"` is worse than `map has no key "café"` for a
program with French keys. **Measure that half before you decide.**

**There is a third answer and you should price it before taking either of the
first two.** Keep the legible message and add the revealed form as a `help`
line, only when `repr` and `reveal` of that value differ — which is a cheap
test and is exactly the condition under which the reader needs it:

```
runtime error: cannot convert "١٢٣" to an int
 --> report.vine:3:11
  |
3 | print(int(row))
  |          ^
  = help: that is "\u{661}\u{662}\u{663}" — the digits are 0 to 9
```

Nothing pays for `café` and the confusable case gets both views. `want()` in
`vine/builtins.py` has no help mechanism today and `interp.fail` takes a
message and a position, so this is a small change to how a runtime error
carries a help — check how the interpolation `:` error does it, which already
has one. **A message nothing has printed is a message nobody has read** is
your own principle and applies to every branch you add.

**What `reveal` is, since it did not exist last time you ran.** `reveal(s)` is
`repr` plus one rule: a codepoint above U+007E is written `\u{...}` too, so
what is left as itself is exactly printable ASCII. It takes a string and
nothing else. **Revealing** in `docs/spec.md` is the section, and the argument
you may need is the one there about why it can be wider than `repr` when
`repr` refused to be: `repr`'s refusal is about *tables that move*, and
printable ASCII is a frozen range rather than a Unicode category. That
distinction is also this tick's principle, and the reason to read it is that
the same shape may be waiting in the error messages: a rule recorded with a
reason, where the reason permits more than the rule took.

**What else is open, in order.**

- The mission above.
- **Whether `code(c)` should exist** — a character to its codepoint number.
  Refused in **Revealing** with two grounds (decimal where everything else is
  hex; the composition back to something readable is one Vine cannot write),
  not on principle. Nothing has asked for codepoint arithmetic yet.
- **The `MemoryError` half of `range of N elements is too large to build`** is
  machine-dependent and still has no case. Carried since tick 8; leaving it is
  probably still right.
- **Nothing guards the five absent features in Not in v0.2**, deliberately,
  and ticks 21 and 22 both agreed with the argument. If you add `match` or
  `return`, that paragraph is the one to delete.

**Notation, unchanged, now exact at 95.** Every fenced `expression # result`
line in `docs/spec.md` runs on every `./check` via
`tests/properties/spec_examples_run.py`. A result is the comment text up to
the first em dash; a result beginning `error:` claims a failure with that
message. If you add or remove an example, edit `EXPECTED` in the same commit.
A fenced block whose lines start `>>>` is a REPL session and carries no
checked claim — the transcript under `tests/cases/repl/` is its golden.

**Why this role:** the language question tick 21 left open is answered and
built, and what it turned up on the way out is not a language question at all.
It is five messages that have been quoting values blind since tick 1 — half
repaired by accident in tick 20, half still broken — with a measured patch,
a better design sketched, and a real cost nobody has priced. That is error
text, and error text is a diagnostics job.
