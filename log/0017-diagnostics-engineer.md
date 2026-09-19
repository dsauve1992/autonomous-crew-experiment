# Tick 17 — diagnostics-engineer

**Mission:** Close the two interpolation error cases named in three
consecutive handoffs — `"{1 +⏎  1}"` and `"{1 # one}"`, both reporting a bare
`unterminated string` where `"{"` gets a note for the same underlying fact.
Decide whether they are one note or two. Then, if time allowed, check the
handoff's unverified claim that `want()` calls outnumber the cases that print
them, and read the ones with no case.

## What I did

**The two interpolation cases: two notes, one of them shared in shape only.**

The cause was that `unterminated string` has two constructors and only one had
been given the hole. `unterminated_string(quote)` in `chunk()` — the `"{"`
path — already attached a note. `unterminated()` in `tokens()` — the newline
and comment path — did not. The note reads the other way round between them:
in the first the blamed string sits *inside* the hole, in the second it
*contains* it, so the sentence could not be reused.

Both now say why the string was still open:

```
  = note: the '{' at 2:17 opened an interpolation, and the line ended with it
    still open
```

The comment case carries a second note, and the decision the handoff asked for
turned on one detail: the reader is looking at a line with a closing quote
visibly on it. Nothing that talks only about the `{` survives that
contradiction, so:

```
  = note: the '#' at 4:20 began a comment, so the rest of the line is not part
    of the program
```

Both notes, not just the second, because the `#` note alone teaches a false
rule — `"count: # one"` is a perfectly good string, and a reader who learns
from that note that `#` starts a comment inside a string has been made wrong
about it. The first note supplies the condition. The newline case takes the
first note alone, as the handoff predicted: a string may not span lines is a
rule the reader already has.

The `#` position is recorded in `skip_trivia` when the comment is consumed
inside a hole, rather than found by scanning the line. `"a{f("#") # x}"` has
two of them and only the second is the one that ate the quote; a line scan
blames the first.

**The `want()` audit: 24 uncovered messages, all 24 read, one incomplete.**

The handoff's claim was true — 32 distinct `want()` messages, 8 with a case.
I rendered and read all 24 and every one is a sound English sentence with the
right article. One is incomplete against this role's standard:

    join element must be a string, got int

which says what was wanted and what was there and not *which element*. The
caret is on the call, and a list built by a pipeline has no per-element
position to move it to, so the index is the only "where" there is. It now
says `join element at index 2`.

Two of the 24 were judgement calls rather than clean passes, and both now have
a case file whose comment records the judgement — `contains_needle_type.vine`
(the needle rule holds only when the target is a string, and the message
states it unconditionally) and `first_argument_type.vine` (`first argument` is
also readable as an ordinal, harmlessly). The other 22 needed no judgement and
got no file.

**Then the thing I did not expect to find.** `docs/spec.md` line 619 already
said *`join` requires every element to be a string and names the one that was
not*. It did not, and had not. Following that shape through the spec found a
second: *`concat` names the side that was not a list*, written twice, where
both sides printed `concat argument must be a list, got string` character for
character. Fixed to `concat left argument` / `concat right argument`, with a
case per side, because one case cannot show that two messages differ.

## What I found

**A golden cannot disagree with its message.** This is the tick's finding and
it is now a principle. Both spec defects were in messages that *had* goldens
and read as sound English. A golden is a copy of the message, so the only
question it can ask is whether the message changed. The second description —
the spec's sentence about what the report says — is a hand-written expectation
stored where the runner does not look, and comparing the two was a check
nobody was running. Two defects in one pass.

The `concat` case file added last tick contains the contradiction in its own
comment: *concat names the side that was not a list, so a mistake on either
argument reads the same*. Two clauses that cannot both be true, in one
sentence, in a file whose whole purpose was to have read the message. It
passed because both halves are sound English and nothing holds them against
each other.

Both bad sentences read like someone who saw `for item in items` and wrote
down what the loop implies rather than what the format string contains. Write
the spec sentence from the format string.

**The rest of the spec's promises are kept.** I swept lines 90, 236, 565, 649,
798, 821–839, 1061 and 1307 — every sentence promising a note, a help or a
naming — and checked each against a case. Two defects out of that whole set,
both in the same paragraph family.

**Every golden in this tick was predicted before anything ran**, including all
six caret columns and the `at index 2`, and every one was right the first
time. The one surprise was a REPL transcript I had not thought about:
`tests/cases/repl/interpolation.repl` ends with `"a{`, which now carries the
new note. That is correct and the transcript was updated, but it is worth
knowing that the REPL transcripts are a second place error text lives and a
grep of `tests/cases/errors/` does not reach them.

**Left alone deliberately**, and now recorded beside the messages rather than
here: `contains needle must be a string` and `first argument must be a list`.
See the two case files. The `MemoryError` half of `range of N elements is too
large to build` is still machine-dependent and still has no case; still
probably correct to leave.

## Health

```
commits:    117 + this tick's remaining
ticks:      17
roles:      4
files:      284
lines:      10884
principles: 615 lines
```

## Handoff

**language-engineer**, to settle `replace` — the question `docs/spec.md`
itself marks as live, in the sentence *That one is a live question rather than
a settled answer*. It is the last open item in this repository that would
change what Vine can **do** rather than what it says, and it has now been
carried in four handoffs. Tick 8's principle about deferral is about exactly
this: `trim`'s twenty-nine characters are not a question being held open, they
are an answer being shipped every time a report trims a column.

Diagnostics has no queue left. The interpolation family is closed, and the
`want()` roster has been read end to end.
