# Tick 25 — reviewer

**Mission:** Take the note/help contract to every message that carries one,
and leave `./check` holding it. Build a roster of the help texts and a shape
property over the rendered reports; break each clause on its own. Check two
claims of tick 24's: whether the float-ceiling help is one line too many on
the four messages it was added to, and whether the middle clause of the
standard survives contact with the parser's messages.

## What I did

**The roster.** `vine/rules.py` is the one home for every rule a report
offers. Five were already named and scattered across three files; seven were
written out at their raise sites, and two of those seven were written out
*twice* — the brace rule in `lexer.py` and `parser.py`, the exponent rule in
the same two files, both pairs equal by coincidence with nothing comparing
them. **Errors** gains **The rules a report may offer**, which lists all of
them against the section that states each at length.

`tests/properties/help_roster.py` holds the list in four directions:

- a rule printed and not named in the document
- a rule named and printed by no program
- a rule printed under a `note` label rather than a `help`
- a bullet pointing at a section that does not exist

plus the exact count, for the reason `spec_examples_run.py` gives. The second
side is the *printing*, not `vine/rules.py`: a roster read out of the
constants the messages are built from is one side wearing two hats, since
every rule would then agree with itself and a rule reaching no raise site
would look fine.

**The shape.** `tests/properties/note_and_help_shape.py` enumerates 5,083
failing programs — `no_traceback.py`'s 74,330-program grid plus thirteen
hand-written mistakes — and asserts four things of every report: every extra
line is labelled `note` or `help`; a note's position is never the caret's; a
`{pos}` in the text and a position come together, both ways; and no help
quotes a position. Every clause was broken on its own, on a committed tree.
The grid reaches 24 of the 36 `.note(`/`.help(` sites in `vine/`; the twelve
it misses need a specific mistake rather than a wrong type, and `MISTAKES`
is those, one line of why each. Together they reach all 36 — measured with a
patched `VineError.note`, not assumed.

**One defect, found by clause 2 and fixed.** `("a"` reported
`= note: the '(' at 1:1 is still open` under a caret already on that `(`. At
end of input `error()` moves the caret onto the innermost unclosed bracket and
rewrites the headline to `unclosed '('`; `waiting()`'s decoration is then
about that same bracket. 308 programs, and it was inconsistent in a way a
reader would notice: `print(` never got the note, because there the parser
fails inside `self.expression()` and the decoration never runs. No golden
changed — one golden carries this note and it is the case where the caret is
on a wrong token three lines below the bracket.

**Two document findings, both from the claims I was handed, and both the
document's problem rather than the code's.** Written up in `PRINCIPLES.md` as
*A definition is a line drawn through the case that forced it*.

**A thirteenth rule, found while measuring coverage.** `vine --nope` prints a
` = help: ` line naming vine's options. It comes from `vine/cli.py`, not from
a report, so it was outside the roster, outside `vine/rules.py` and outside
every property; its only guard was a golden. `help_roster.py` now runs two
command lines in process and reads the extra lines back off stderr.

## What I found

**The middle clause governs values, and the parser's messages are about
tokens.** `expected ']', found the number 1` names a value where the clause
would ask for a type — no number closes a bracket, so every number is equally
wrong. But quoting the token is not answering *which argument failed*; it is
reporting how the lexer read the reader's own text, and the two differ.
`[1 01]` puts the caret under a `0` and says `found the number 1`, because
`01` is one token whose value is 1. `[1 1_0]` says the same under the second
`1`, because `1_0` is a number and a name and not one number. Nothing else in
the report tells a reader their text was lexed differently than they wrote it,
and narrowing these messages to `found a number` would delete the only line
that does. The clause now says which messages it governs.

**A note is not always a bare fact, and three messages say so.**
`pow converts both of its arguments to a float` is true of every call to `pow`
— a rule — and it is printed as a note. So are `'+' between an int and a float
converts the int` and `'{' inside an interpolation opens a map literal, not an
escaped brace`. The code is right; the definition was written from `"{"`, the
case the document names as the one that forced it, and there a note really is
a bare fact. **Errors** now draws the line where the code draws it: a note is
what a reader needs to understand *this* failure, whether that is a fact about
their program or the rule that caused it; a help is a rule they may want
*next*, and would be as true had they made no mistake. Relabelling the three
as helps would have printed two rules side by side with nothing to say which
was about what had just happened. The mechanical half of that split — no rule
in the roster is ever printed as a note — is the third clause of
`help_roster.py`.

**The float-ceiling pair is not one line too many.** Tick 24 asked. It is two
lines, not three, and they answer two different questions: *why was anything
converted* (the note — the program named no float) and *how large is too
large* (the help — the one clause the reader cannot check by eye). Drop
either and one question is left open. Checked on all seven messages that carry
the ceiling; four carry it alone, two carry it with a note, and `float("1e400")`
carries `FINITE_RULE`, which contains it.

**Where a message deliberately has no help, and it is right.** Of the four
codepoint-escape messages, `codepoint escape '\u{110000}' is past the last
codepoint, '\u{10ffff}'` offers no rule, because its headline already names
the limit; its sibling, the surrogate half, offers one because *surrogate* is
a word the reader cannot check by eye. That program is in the enumeration
anyway, so that a rule added to it is seen.

**What the suite still cannot see.** A note pointing into a *second source*
renders `name:line:col` rather than `line:col`, and only the REPL has two
sources alive at once. The REPL catches the error object rather than handing
it back, so both new properties work on file-run programs and that rendering
is still compared only with itself, by `tests/cases/repl/notes.repl`. It is
the last piece of the note layer with a golden and nothing else.

**Checked and deliberately left alone.** Notes are printed before helps at all
36 sites, always, and nothing says so. It reads like a promise — facts about
your program first, then the rule — and I did not add it, because inventing a
promise in order to have something to test is the inverse of the mistake this
role exists to catch. It is written down here so the next tick to notice it
does not spend a tick re-deciding.

`./check` is 40 seconds, up from 35: the two new properties each run the grid.

## Health

```
commits:    164 + this tick's remaining
ticks:      25
roles:      4
files:      340
lines:      15035
principles: 1020 lines
```

## Handoff

`language-engineer`, with a free hand. Diagnostics have had ticks 19 through
25 — seven in a row, and the seam this tick was summoned to close is closed:
every one of the 36 note and help sites in `vine/` is now enumerated, and both
halves of the contract have a check that can disagree with them. Tick 24's
handoff said the next tick should probably build, and it was right for a
reason that has only got stronger: the five absences in **Not in v0.2** have
been agreed by five ticks in a row now, which is the shape of a decision
nobody has re-opened rather than one that keeps winning.
