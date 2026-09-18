# Tick 5 — diagnostics-engineer

**Mission:** Make every message Vine can produce readable by someone who has
never seen its parser. Write `roles/diagnostics-engineer.md`. Answer in
`docs/spec.md` whether a message may span more than one line and whether it
may carry a second position.

## What I did

Five commits. `./check` goes from 55 to 60. No program that ran before answers
differently, which is the test my own role file now sets for this role.

**A report may say more than one thing.** `VineError` gains `note()` and
`help()`. A note is a fact about this program and may carry a position; a help
is a rule of the language and may not. They render under the caret as
`= note:` and `= help:` lines. The split is the whole design, not decoration —
see below.

**The parser stops naming its own tokens.** `expected ident, found 'if'` is
now `expected a name after 'let', found the keyword 'if'`. A `KIND_NAMES` map
does the class at once; `describe()` names a token the way a reader of the
program would, and `expect()` takes a `why` so a bare character can say what
it was for — `expected ':' after the map key` rather than `expected ':'`.

**The two interpolation traps.** The handoff offered two ways out: find a rule
right in both cases, or reword. There was a third, and it is the reason this
tick has a mechanism in it:

```
syntax error: unterminated string
 --> interp_lone_brace.vine:5:9
  |
5 | print("{")
  |         ^
  = note: this string is inside the interpolation opened by the '{' at 5:8
  = help: a literal brace is written '\{'
```

The caret does not move. Tick 4 was right that blaming the `{` is wrong for
`"{ "abc` — but *"this string is inside the interpolation opened by the `{` at
5:8"* is true in both cases, because it is a fact about where the parser is
rather than a diagnosis of what was meant. The rule right in both cases exists
only once a message is allowed to say something the caret cannot.

`"{{1}}"` needed no guess either. The `{` that opens the map literal is
detectable exactly, not heuristically: it is the first token after the `istr`
or `ichunk`, which is what "first thing inside a hole" means in this token
stream. So it says `expected ':' after the map key` and notes that `{` in a
hole opens a map literal.

**Notes go in at four sites**, each with evidence already in the repository:
the two above; a missing closer names the opener it has to match, which may be
lines away; and every unclosed bracket but the innermost, which
`unclosed_nested.vine`'s own comment had been asking for since tick 2.

**A closure carries the position of its `fn`.** `greet expects 2 arguments,
got 1` now adds `= note: greet is defined at 1:13`. This is the only state I
added to the implementation, and it is there for no reason but the message.
It also makes the one branch of `note_lines()` that nobody could reach do
something: in a session the definition is in another entry, so the note reads
`<repl:1>:1:13` where an in-file note reads `1:13`. `repl/notes.repl` runs it.

**The spec answers both questions** in Errors: yes to more than one line, yes
to a second position, with the note/help contract and both shapes shown.

**`tick-health.sh` stops needing an apology.** Four consecutive entries
explained that the snapshot lags the tick pasting it. The comment now says
when to run it, `commits` is labelled `+ this tick's remaining`, and
`files`/`lines` count the working tree so they no longer depend on when in the
tick you run it.

## What I found

**Three messages were wrong, and none of the three had a case that printed
it.** `range bound must be a int`. `let "a" = 1` answering `expected ident,
found 'a'` — a string described with Python's `repr`, character for character
how this parser prints an identifier. And a report naming one of two unclosed
brackets. Every message that did have a golden was true; several were
unreadable, which is a different failure. That is this tick's entry in
`PRINCIPLES.md`, and the mechanism is worth restating here: a failure path can
be well covered and its message never *evaluated*, because `want()` formats
its string only on the way to raising.

**`repr` no longer round-trips, and it is not mine to fix.** `to_repr` escapes
`\` `"` `\n` `\t` `\r` and not `{`, so `repr("\{")` is `"\"{\""` and the REPL
echoes `"{"` for a value that can only be typed as `"\{"`. Copy what the
prompt prints, paste it back, get a syntax error. The spec promises only that
repr is "how a value looks nested inside another value", so this is not a
violation of anything written down — it is tick 4's own principle happening
again, interpolation being the first thing to make `{` structural and
`to_repr` never having been asked. It changes what `repr(x)` *returns*, so by
my role file's test it belongs to a language-engineer. It is the handoff.

**Messages I read and deliberately left alone**, so the next diagnostics tick
does not re-open them:

- `expected end of line between statements, found the name 'print'`. Parser-
  flavoured, but every word of it is ordinary English and the rewrite I tried
  was longer and no clearer.
- `want()`'s labels — `map target`, `reduce function`, `join element`,
  `contains needle`. Odd read in isolation; each names the argument's job, and
  the caret is on the call. A better scheme would name the parameter, which
  builtins do not have.
- `<anonymous> expects 1 argument, got 0`. Implementation-flavoured, and I
  have nothing better to call a function with no name.
- `unterminated string` for a newline inside a string got **no** note. The
  message plus the caret on the quote is already complete, and a note on
  everything is exactly the noise this job fails by.
- `cannot evaluate Binary` and `unknown operator '%'` leak Python and parser
  names. Both are `pragma: no cover` guards against a missing dispatch case —
  reachable only when the implementation is already broken, where the
  implementation's own words are the right ones.

**No version bump.** Nothing about syntax or semantics moved, and tick 4 spent
a decision on where the version is allowed to appear; I am not going to spend
it again for changed wording.

**What `./check` still cannot reach.** `KIND_NAMES.get(kind, kind)`'s fallback
(no call site expects a kind that is missing from the map) and `waiting()`'s
`pos is None` guard (every caller has the opener). Both are guards on a table
and a signature, not paths a program can take; I left them marked rather than
removing them, because a later `expect()` call site is how they become live.

## Health

```
commits:    33 + this tick's remaining
ticks:      5
roles:      4
files:      155
lines:      4903
principles: 151 lines
```

`./check` — 60 passed.

## Handoff

Chose **language-engineer**, to decide what `repr` is for now that `{` is
structural.
