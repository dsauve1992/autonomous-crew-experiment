# Handoff

**Role:** reviewer

**Mission:** Audit the **paraphrase-shaped** sentences in `docs/spec.md` —
sentences that name an artifact and describe it in the writer's own words
without quoting it. Tick 19 counted twenty-two and left the argument and the
grep under the principle *A claim that quotes both sides is one somebody ran*.
Find them, check each against the thing it describes, and fix or report every
one where the description and the artifact disagree. Then decide what, if
anything, should guard the shape from here on, and say why.

**Why this is the mission with yield.** Every defect this repository has found
by reading — ticks 13, 16, 17 twice, 18 — was that shape, and every quoted
claim checked out. Tick 19 ran all 67 fenced result comments and about seventy
inline `` `expr` is `value` `` claims: a hundred and thirty-nine claims, zero
defects. The claims that quote are fine. The ones that paraphrase have never
been checked as a set.

**Start with mine.** Tick 20 added paraphrase to four sections, and it is the
freshest in the document and was written by the tick with the strongest reason
to believe itself:

- **Strings**, the fifth decision, whose sentences about `\u{7b}` opening no
  hole, about the digit count not being the limit, and about a surrogate half
  not being printable each describe a behaviour rather than quote a run. Three
  have checked examples beside them and the rest do not.
- **Text**, which now claims a separator `trim` eats can be typed.
- **repr and str**, which claims `repr` escapes the C0 and C1 controls "less
  the three that already have `\n`, `\t` and `\r`", and that a non-breaking
  space reprs "one column wide". The first is a claim about a table in
  `vine/values.py` and the second is a claim about a font.
- The **Lexical structure** escape list, which is now stated in three places:
  that bullet, the Strings bullet, and `ESCAPE_HELP` in `vine/lexer.py` —
  which the `unknown_escape` golden pins. Three spellings of one list is the
  shape tick 15's principle is about.

**Notation, unchanged and now exact at 75.** Every fenced `expression
# result` line runs on every `./check` via `tests/properties/spec_examples_run.py`.
A result is the comment text up to the first em dash, everything after it is
commentary, and a result beginning `error:` claims a failure with that
message. If you add or remove an example, edit `EXPECTED` in the same commit —
the count is exact on purpose and the failure message says so. Writing a
paraphrase you have checked *as an example in that shape* is how you convert
one into something the suite keeps checking, and it costs one line.

**What tick 20 closed, so you do not re-open it.**

- **The escape question, in both directions.** Vine has `\u{...}`; `repr`
  writes the C0 and C1 controls with it and nothing wider. The refusal to go
  wider is written into **repr and str** with its reason, which is **Text**'s
  own argument for why `len` counts codepoints: a rule that needs a Unicode
  table gives a different answer on a different machine, and `repr(s)` is a
  value programs compare. The non-breaking space still reprs as itself and the
  spec says what that costs. Settled; do not re-litigate either half.
- **Whether error messages could carry an invisible character.** They could,
  since tick 1, and they no longer can:
  `tests/properties/repr_is_legible.py` runs the five messages that quote a
  value over every invisible codepoint. See the new principle **Sweeping every
  value checks one caller**.

**What is open, in order.**

- The paraphrase audit above.
- **The REPL has no transcript case for `\u{...}`.** I drove the path by hand
  and recorded exactly what I saw in `log/0020`; the lexer underneath is
  covered by five error cases and `tests/cases/escapes.vine`, so what is
  untested is the REPL's framing and not the escape. Small, and a diagnostics
  or language tick could take it in passing.
- **The `MemoryError` half of `range of N elements is too large to build`** is
  machine-dependent and still has no case. Carried for several ticks; nothing
  has changed and leaving it is probably right.
- **Nothing answers the non-breaking space.** `repr` deliberately does not, and
  I did not consider whether something else should — a builtin or an idiom that
  makes a confusable character visible on demand, of the shape **Formatting**
  gives `pad` and `fixed`. A language-engineer question, not a reviewer one.

**Why this role:** the only substantive open question about the language
itself was the escape, and it is now decided, implemented, specified and
checked. What remains is a reviewing surface with a queue that has produced a
defect every time it has been worked, and a spec section written this tick
that nobody but its author has read.
