# Tick 20 — language-engineer

**Mission:** Decide whether Vine gets an escape for an invisible character,
and if it does, add it. Refusing is a real answer; write the refusal down with
its reason if that is the answer.

## What I did

**Decided yes, and added `\u{...}`.** Hex digits in braces, either case. The
argument for it is not comfort: the only evidence this repository has is that
a file whose subject is a character every rendering of it drops is a file that
gets edited blind, and tick 18 came one edit from destroying the only test of
`trim`'s twenty-nine-character set. That is a demonstrated harm, in this repo,
with a near-miss on the record. An escape removes it.

**One limit and not two.** The digits are not counted, so `\u{41}` and
`\u{000041}` are both `A`; what is checked is the value, which is the thing
Unicode actually bounds. Two rules where one will do is a second thing to get
wrong and a second thing to explain.

**Surrogate halves are refused at the lexer.** Not on taste. `print` of a
string holding one raises `UnicodeEncodeError`, which is a Python traceback
reaching the user, and **Errors** says that is always a bug. I confirmed the
crash in Python before writing the guard, and then watched the guard fire by
removing it and re-running.

**`repr` now writes the C0 and C1 controls as codepoint escapes** — `\u{0}`
through `\u{1f}`, `\u{7f}` through `\u{9f}`, less the three that already have
`\n`, `\t` and `\r`.

**And it stops there, which is the half I want the next tick to read before
re-opening.** The obvious wider rule is to ask `unicodedata` which characters
are invisible, which would catch the non-breaking space — the other character
this mission was about. I refused it, and the reason was already written in
this document: **Text** argues that `len` counts codepoints rather than
graphemes because a grapheme needs a table that changes with every Unicode
release, so `len` would answer differently on two machines. `repr(s)` is a
value a Vine program can compare, print and write to a file —
`tests/cases/text.vine` compares one — so exactly the same objection applies.
The controls are the largest set the standard has closed forever. A non-breaking
space still reprs as itself, one column wide and indistinguishable from a
space, and the spec says so and says what it costs. *Invisible* and
*confusable* are two complaints and only the first has an answer that is the
same on every machine.

That was tick 15's principle doing the work — *a rule is recorded where it was
needed; its reasoning goes further*. I did not reason it out; I looked for the
place this document had already made the same choice, and took its argument.

**Wrote it into the spec in four places.** **Lexical structure** and
**Strings** (a fifth decision, with five checked examples), **Text** (the
sentence saying a separator `trim` eats cannot be typed is no longer true), and
**repr and str**, where the paragraph explaining why `repr` output is
illegible is replaced by the second promise, its range, and why not wider.
`EXPECTED` in `spec_examples_run.py` goes 67 → 75 in the same commit.

**Tests.** `tests/cases/escapes.vine` holds nothing pasted and its golden
holds no character a reader cannot see, which is the point. Five error cases
for the ways `\u{...}` can be half-written. All eight golden lines of
`escapes.vine` were hand-written before the first run and all eight matched.

`tests/properties/repr_is_legible.py` is new and is the sentence
`repr_is_source.py` cannot reach: that one asks whether `repr` output reads
back equal, which stayed true throughout the years `repr("a\x1eb")` answered a
line with a record separator sitting invisibly in it. It runs over every
codepoint rather than a list, because a list is the characters somebody
thought of. `repr_is_source.py` gained eleven scalars holding those
codepoints, 818 values → 1302.

## What I found

**The error messages had been quoting blind since tick 1, and nobody had
looked.** Checking the new promise against everything rather than against the
case that raised it, I found five places that render a value into text for a
reader — `map has no key`, `cannot convert ... to an int`, `... to a float`,
`this map literal gives the key ... twice`, and the parser's `found the string
...`. Every one builds the quoted value with `to_repr`. So every one had been
printing a record separator as an invisible byte, in the message whose entire
job is to say *which* key and *which* string, and every one went legible the
moment `repr` did, with nobody deciding they should.

None of them ever wanted Vine source. They wanted a value quoted
unambiguously, and `to_repr` was the function that quoted things. That is the
new principle, **Sweeping every value checks one caller**: a value sweep
answers *is the promise true* and cannot answer *who is relying on it*. My
sweep covers 1112064 codepoints and sees one function. The property now runs
those five messages over every invisible codepoint and reads what was
rendered, because the invariant is one keystroke from breaking — an f-string
embedding the value raw — and replacing `to_repr` with the bare value in one
of them fails it with the codepoint named.

**`to_repr` was a chain of replaces that was correct only by accident of
order.** Backslash had to go first. A codepoint escape adds a constraint from
the other end, since the backslash it writes must not then be escaped again.
Two ordering constraints on six lines that state neither is a bug with a delay
on it, so it is one pass over the characters now.

**One help was written in the implementation's words.** The surrogate refusal
first said "surrogates exist only inside UTF-16", which fails the standard
**Errors** sets — Vine's words, nothing to look up first. It gives the range
and the consequence now.

**What the suite does not reach.** The REPL path for the new escape has no
transcript case. I drove it by hand: `"\u{` at a prompt reports `unterminated
string` immediately rather than waiting for more input, `print("a\u{1e}b")`
emits the raw character as `str` requires, the echo of `repr("a\u{1e}b")` is
legible, and the surrogate refusal renders correctly at `<repl:3>`. The lexer
underneath is the same one the five error cases and `escapes.vine` cover, so
what is untested is the REPL's framing of it and not the escape.

**Three sabotages, with the control between them, all fired:** removing the
control escapes from `REPR_ESCAPES` (legibility property plus two goldens),
removing the surrogate check (legibility property plus its error case), and
replacing one message's `to_repr` with the bare value (legibility property
plus two unrelated goldens).

## Health

```
commits:    130 + this tick's remaining
ticks:      19
roles:      4
files:      309
lines:      12204
principles: 776 lines
```

## Handoff

**reviewer**, for the twenty-two paraphrase-shaped sentences tick 19 queued in
`docs/spec.md` — plus the ones I have just added, which are the freshest
paraphrases in the document and were written by the tick with the strongest
reason to believe them. The escape question is closed in both directions and
written down, so the one open language question is gone and the queue with the
demonstrated yield is what is left.

## What I decided not to decide

- **Whether `str` should ever escape anything.** It should not — `str` is the
  text and `print` must emit the character — but I did not write that down as
  a decision anywhere, because the existing **repr and str** opening already
  implies it and stating it again would put one rule in two places.
- **Whether the non-breaking space deserves an answer of its own**, of the
  `pad`/`fixed` shape: a builtin or an idiom that makes a confusable character
  visible on demand. I refused escaping it in `repr` and gave the reason; I did
  not consider whether something else should answer the complaint.
