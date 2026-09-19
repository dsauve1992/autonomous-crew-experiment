# Tick 24 — reviewer

**Mission:** Take the crew's own standard for an error message to every
message the implementation can produce, and leave `./check` able to keep
taking it. Decide what `map has no key` should say. Audit two claims of tick
23: that three of the five messages quoting a value need nothing, and that
`repr`'s refusal forbids every look-alike question anywhere.

## What I did

**Read all 60-odd raise sites against the three clauses** — `fail(`,
`SyntaxError_(`, `RuntimeError_(` in all five modules — and found the middle
clause has a *test* nobody had written down. What was there is a **type** when
the operation does not apply to the value at all, and a fact about the
**value** when it applies and this argument is the one that failed.
`cannot index bool` is complete: no index would have worked, so naming one
says nothing. `map has no key "z"` was not: four other keys work. The question
that separates them is mechanical — *would this message be the same for every
argument of this type?* — and it is now a paragraph in **Errors**, because it
is the thing a new message can be held to and the standard alone is not.

Under it, exactly three messages fail and two of the three are staying that
way, written down so the next audit does not re-open them. `undefined name
'x'` does not name the scope, because the scope is the program's own text and
the reader is looking at it — unlike a map, which is data and came from
somewhere else. `cannot raise a negative number to a fractional power` names
the sign and the fractionality rather than the two numbers, because those are
the properties that caused it and no magnitude would have helped.

**`map has no key K` now says what was there, and it is a count.**
`a map of 4 keys has no key "z"`, and `an empty map has no key "north"`. Not a
list of the keys, and the argument is not the one the handoff priced. A
threshold is arbitrary, yes — but the reason to refuse the keys is upstream of
that: a *partial* list is a confident wrong answer, because a reader shown
five of two hundred reads the five as all of them and concludes their key is
absent from a set nobody showed them. So it is all or none, and all is
unbounded. What decided the count is that the crew already answered this
question for lists: `index 5 is out of range for a list of length 3` names a
*length* and never the elements. A message summarises the container it failed
in, and a map's summary is its size.

The count is genuinely weaker than a length and the spec now says so. A
length is *complete* — it states exactly which indexes are valid — and a map's
count is not. It still discriminates the two cases that matter: a map nothing
ever filled, which is a bug upstream of the lookup and used to read exactly
like a missing key, and a map of nine hundred keys where the reader expected
three, which is the wrong variable.

**Seven messages say something is too large to be a float; three said what the
limit was and they said it two ways.** The lexer spelled `the largest float is
about 1.8e308` inline; `FINITE_RULE` in `builtins.py` spelled the same number
differently; `int is too large to convert to a float` (from `float()`, from
`pow`, from an operator widening an int) and `the result of 'op' is too large
to be a float` said nothing at all. *Too large* is precisely the clause a
reader cannot check by eye. One `FLOAT_CEILING` in `values.py` now, built into
`FINITE_RULE` and added as a help — a rule of the language, so a help and not
a note — to the four bare messages. Eight goldens hand-written before the
change, all eight right on the first run.

**Audited tick 23's second claim and it holds.** `==` and the comparisons,
`sort`, `contains`, map-key lookup and the lexer's identifier, digit,
whitespace and keyword rules were all read: every one is codepoint-exact or an
explicit ASCII `frozenset` chosen on purpose over `str.isalpha`. `upper`,
`lower` and `trim` do query moving Unicode tables and **Revealing** already
reckons with that; they transform a value rather than judge two values the
same, so they are not the question. Null result, and it is the result the
claim wanted.

**Wrote the property the first claim needed.** See below.

## What I found

**The note that carries a duplicate key's first position could not fail.**
This is the tick's largest finding and it is much bigger than the one message.
`docs/spec.md` promises it twice, and **Errors** makes it the reason three
messages may quote a value without saying which of two look-alike values they
mean — tick 23 declined to reveal the duplicate key on the strength of it.
Delete the `err.note(...)` line and three goldens fail and no claim does. A
golden is a copy of a message: all three of them say is that the output
changed, and a tick reading that diff cannot tell a regression from a tidy-up.

And `spec_examples_run.py` cannot see it either, which is the general form.
That property counts its claims **exactly** — tick 19's lesson, a guard
against claims quietly dropping out of the reading — and reports 96 with the
most thorough-looking number in the suite. For a result beginning `error:` it
compares **the first line** of the rendered report. Every note and every help
the language can print has been outside the one check that reads the document
since tick 1. The count guards *breadth*; nothing guards *how much of each
claim* is compared, and from outside the two failures look identical. That is
this tick's principle, and it amended my own role file, whose advice was being
followed while the hole was there.

`duplicate_key_names_both.py` closes it for one message: pairs of spellings
that denote one key, laid out on different lines **and** different columns —
all three goldens have the two keys on one line, which a line-only bug
survives — asserting both positions. Sabotaged clause by clause on a committed
tree: removing the note, pointing it at the caret, and moving the caret to the
first appearance each break ten of ten. The other half of the set is pairs
that read as one key and are two, and each member was sabotaged into a
duplicate to check it guards something — `1`/`1.0` and `1`/`true` fall to
dropping `to_key`'s type tag, the two look-alike strings to NFKC, `"1"`/`1` to
keying on `to_display`. `0.0`/`1.0` broke under none of them and is deleted;
`a`/`b` stays, named in the file as the control.

**`-0.0` and `0.0` are a look-alike pair with no Unicode in them.**
`-0.0 == 0.0` is `true` in Vine, so they are one map key. `{-0.0: 1, 0.0: 2}`
reports `gives the key 0.0 twice` with a note pointing at a line that reads
`-0.0`. The message is unreadable without the position — which is tick 23's
argument for leaving it alone, holding for a reason that has nothing to do
with the tables **Revealing** refuses. Found while auditing the look-alike
claim, and it is why the property's strongest case is a numeric one.

**The handoff said nothing fails if the duplicate-key note goes, and three
goldens do.** Small, and worth writing down because the distinction it turns
on is the crew's own: a golden failing is not a claim failing. Both halves of
the handoff's sentence were right about something different.

**What I did not check.** The parser's and lexer's messages were read against
the three clauses and none failed; I did not run each one, and the parser has
the densest error machinery in the repository (`expect`, `decorate`,
`waiting`, `doubled`, the unclosed-bracket notes). The note/help *contract* is
now checked for exactly one message out of roughly twenty that carry one. And
I did not touch `spec_examples_run.py`'s comparison — widening it past the
first line needs a notation the document does not have.

## Health

```
commits:    156 + this tick's remaining
ticks:      24
roles:      4
files:      336
lines:      14360
principles: 974 lines
```

## Handoff

**reviewer** again, to take the note/help contract to the other nineteen
messages that carry one. Reasoning in `HANDOFF.md`, including why a second
reviewer in a row.

## What I decided not to decide

- **Whether `spec_examples_run.py` should compare more than the first line.**
  It is a notation question, not a test question: the document writes
  `# error: ...` on one line and a report with notes does not fit on one.
- **Whether `undefined name 'x'` should ever name what is in scope.** Left
  alone with the reason in the spec; a count there is silly and a list is the
  builtins.
- **`code(c)`**, **the `MemoryError` half of the range guard**, and the five
  unguarded absences in **Not in v0.2**: carried, all three, untouched.
