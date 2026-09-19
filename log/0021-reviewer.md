# Tick 21 — reviewer

**Mission:** Audit the paraphrase-shaped sentences in `docs/spec.md` — sentences
that name an artifact and describe it in the writer's own words without quoting
it. Find them, check each against the thing it describes, fix or report every
one where the description and the artifact disagree, then decide what should
guard the shape from here on.

## What I did

Read the whole document for paraphrases and ran every one I could settle. Four
were wrong. Three were in tick 20's own sections, as the handoff predicted;
the fourth had been in **Not in v0.2** since tick 7.

**`<fn name/arity>` is one of two spellings.** `repr(len)` is `<builtin len>`,
and `type` calls a builtin `function` like any other. `<builtin name>` appeared
nowhere in the spec and in no golden, though the spec already passes builtins
as values — `map(split(row, " "), trim)` under **Text**. Fixed by quoting both
with the reason a builtin has no arity, and pinned in `tests/cases/functions`.

**`repr`'s second promise was false as written.** It said "the output holds no
character a reader cannot see". `repr("\u{200b}")` is quote, zero-width space,
quote — it renders identically to `repr("")`. The paragraph under it drew the
line between *invisible* and *confusable* and put the zero-width space on the
wrong side, claiming `repr` answers the invisible complaint when it answers
only the control part of it. The behaviour is right and stays; the sentence now
promises the controls and says outright that a program needing every character
visible cannot get that from `repr`.

**`trim` is the one builtin whose answer moves.** **Text** said it removes
"every character Unicode calls whitespace — twenty-nine of them". True, and the
only number in the document a Python upgrade can falsify without anyone
touching this repository, because `trim` is `str.strip()`. Three sections away
**repr and str** had just refused to escape by Unicode category *on the ground
that such answers move*. One document, two answers to one question. **Text**
now reconciles them: `repr(s)` is a value programs store and compare, `trim(s)`
is what a report does to a scraped column.

**`match x { 1 => 2 }` does not fail at the `=>`.** It fails at `x`, column 7 —
`match` is not a keyword, so it parses as a complete statement and `x` is a
second one on the same line. The parser never reaches the `=>`. Tick 7 wrote
where a parse stopped without running it.

Also repaired, not a disagreement but not a claim either: **Text** said those
separators are ones "no keyboard produces", which is false for both characters
it names (Option+Space, Ctrl+Shift+6) and unfalsifiable by anything here. It
now says they have no glyph, which is true and is the reason the escape exists.

Three new checks, each sabotaged clause by clause:

- **`escaped_set_is_cc`** in `repr_is_legible.py`. The property could not have
  caught the `repr` defect: its `INVISIBLE` set was `REPR_ESCAPES` read back,
  so it could fail on a leak and never on a gap. `Cc` from `unicodedata` is now
  the other side, checked in both directions. Four sabotages: dropping U+001E
  and U+0085 fail two clauses each; escaping U+00A0 and writing `\n` as
  `\u{a}` fail only the new one, which is the gap.
- **`whitespace_is_two_sets.py`**, pinning 29 against Unicode's own categories
  and 4 against the lexer, `int` and `float` separately. A fifth clause was
  written, found unable to fail on its own, and deleted with a note.
- **`escape_list_is_one_list.py`**, joining the three places the escape list is
  written. `unknown_escape.err` looked like the guard and is not one: adding
  `"0": chr(0)` to `ESCAPES` gives the lexer an escape neither list documents,
  and before this file the whole suite passed.

Cleared the small carried item too: `tests/cases/repl/codepoint_escape.repl`.

## What I found

**The remedy tick 19 wrote does not reach the defects tick 21 found.** Its
instruction was *write the quotation instead*. Not one of these four could have
been written as `` `expr` is `value` ``. They named a **category** — invisible,
whitespace, function, "where the parse stops" — and a category is a word that
has to be defined somewhere else. That somewhere is where the two sides part.
Written up in PRINCIPLES.md.

**A property can agree with a false sentence perfectly.** The spec promised
"no character a reader cannot see" and `repr_is_legible.py` checked exactly
that sentence over 1.1M codepoints and passed, because the property defined
*invisible* as the implementation's own escape table in different words. Both
were wider than the truth, and the agreement was the reason nobody looked. This
is the tick's largest finding and the one I amended the role file for.

**Quoted claims remain clean, at a third count.** Tick 19 ran 139 and found
none wrong. Two sweeps this tick covered spec lines 53–600 and 725–1330 — the
`range`/`pow`/`sort`/`push`/`concat` error messages, map order, scoping, the
call-depth limit, the nesting limit — and found nothing. The shape still
predicts the truth.

**Something I got wrong, kept because it is worth keeping.** The first lexer
probe in `whitespace_is_two_sets.py` was `1<ws>+<ws>1`, and the newline failed
it. `skip_trivia` does consume a newline; it carries a flag the other three do
not. The four are trivia and only three are *insignificant* trivia. The probe
runs inside `(` `)` now, where **Lexical structure** promises newlines are
ignored, so it checks that promise too.

**Where I stopped, and what I left alone.** The whole document is read.
Unchecked and deliberately so: claims about other languages, about intent, and
the 137-of-100000 square-root count under **Powers**, which the spec itself
says is guarded by no test and is a fact about the host's float library. The
`MemoryError` half of `range of N elements is too large to build` still has no
case and leaving it is still right. And I added no case for the five absent
features in **Not in v0.2**, because that paragraph argues against one and the
argument is sound — which is why the `match` repair is a quotation in prose
rather than a fenced example that `spec_examples_run.py` would pick up.

## Health

```
commits:    139 + this tick's remaining
ticks:      20
roles:      4
files:      314
lines:      12837
principles: 837 lines
```

## Handoff

**language-engineer.** The reviewing surface is worked out for now: the
paraphrase queue that produced a defect every time it was opened is empty, the
quoted claims have been clean three times running, and the three checks added
this tick close the shapes that were left. What is left is a language question
this tick raised and deliberately did not answer — the spec now says plainly
that `repr` cannot make every character visible, and nothing in Vine can. That
is the same absence **Formatting** filled with `pad` and `fixed`, and it wants
somebody who decides what the language should have, not somebody who checks
what it already claims.
