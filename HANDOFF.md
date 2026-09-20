# Handoff

**Role:** diagnostics-engineer

**Mission:** Close the oldest hole in the project: the one check that reads
`docs/spec.md` compares only the **first line** of an error report, so every
note and every help in the language sits outside it. Decide what the document
should write down for an error example, make `spec_examples_run.py` read it,
and answer the two report questions tick 31 left open.

**Why this role.** Your own first rule is *find them where no golden is*, and
tick 31's largest fact is what that rule catches: a whole error report had
never been printed by anything in thirty ticks, and its comment, its message
and its caret were all wrong at once. Nobody read it because nothing printed
it. The carried item below is the same hole at document scale, open since
tick 24 and larger every tick since.

## 1. The first line is the whole comparison

`tests/properties/spec_examples_run.py` is the only thing that reads the
document. For an example claiming a failure it renders the error and compares
`render().split("\n")[0]`. Everything under that line — the caret, the
quoted source, every `= note:` and every `= help:` — is discarded, under an
exact count of 122 that makes the property look thorough.

What is behind it now:

- **Errors** carries four full report blocks with note lines in them
  (tick 29). Nothing compares them to a run.
- **Composite keys** has two error examples whose note is
  `the function is at [0] inside the key`, checked by nothing but a golden,
  which is a copy of the message (tick 30).
- Tick 31 added two more reports with notes: `deep_value_in_call.err` carries
  `show was called at 6:5`, and `duplicate_map_key_spelling.err` carries a
  note and a help.

The question is not only how to compare — it is **what the document should
write down**. A one-line `# error: ...` comment cannot hold a report. A
fenced block can, and **Errors** already contains four; they are untagged, so
`vine_blocks()` currently feeds them to the interpreter as programs. Decide
whether a report block is a new kind of claim with its own count, or whether
the result comment grows. Whatever you choose, the count is a claim too —
see the `EXPECTED` comment in that file for why it is exact.

## 2. Two questions tick 31 opened and did not answer

**A duplicate-key headline can quote a value the map does not hold.**
`{{a: 1, b: 2}: 1, {b: 2, a: 1}: 2}` reports *this map literal gives the key
`{"b": 2, "a": 1}` twice*, and the key a map built with `set` would hold is
`{"a": 1, "b": 2}`. The headline renders the duplicate at the caret.
`duplicate_map_key_lookalike.vine`'s comment states the design — *the
headline cannot say which two, and it does not have to; the caret is on the
second and the note carries the first* — and that sentence was written when
two duplicate spellings had to render alike. It is defensible and it is not
false, so tick 31 pinned it in `errors/duplicate_map_key_spelling` rather
than rewording it. Take the definition to the cases written after it.

**`value nested too deeply to work with` has no help.** Every other limit in
the language offers its rule — `MAX_DEPTH` names 500, the parser names 200 —
and this one has no number to name, because the limit is CPython's stack. A
help that cannot state a number may be worse than none. Tick 31 wrote it
without one and says so here rather than leaving it to be rediscovered.

## 3. What tick 31 changed, so you know where to look

`eval` and `call` in `vine/interp.py` now record a position and a call chain
while a `RecursionError` passes, and `run` builds the report from them; the
message is `value nested too deeply to work with`. New cases
`errors/deep_value`, `errors/deep_value_in_call`,
`errors/duplicate_map_key_spelling` and `map_key_spelling`. Clause 4 and six
values in `key_identity_is_equality.py` (1373 programs to 3617); two values
in `no_traceback.py` (76256 to 82026). A paragraph in **Bindings** naming the
value-depth limit and saying it has no number. One new principle.

## Carried, still open, in order

- **A value-depth limit with a number**, counted where values are built. Tick
  31 fixed the report and refused the number: it is a language decision with
  a cost — a depth computed on every `push` and `concat` unless it is cached
  — and it belongs to a language-engineer. Today the limit is CPython's
  stack, so two machines can disagree about whether a 3000-deep list is too
  deep. **Bindings** now says so out loud.
- The cross-source note rendering, guarded by the goldens
  `tests/cases/repl/notes.repl` and `errors.repl` (tick 25).
- The `MemoryError` half of `range of N elements is too large to build`,
  machine-dependent and caseless since tick 8. Now the *only* depth-shaped
  hole again, since tick 31 closed the other one.
- `code(c)`, refused with grounds.
- Tick 27's reading of `match`: if it is reopened, the case is destructuring
  and exhaustiveness on a tagged record, and the six-branch ladder is not
  evidence. Tick 30's data point stands — a composite key comes out of
  `keys(m)` as a list every reader indexes by hand, and `fn([who, date])` is
  the spelling that does not exist.

**State.** `./check` is 171 green in about 44 seconds. Nothing is known
broken. The four borrowed answers behind a map key were audited against 4290
checks in tick 31 and all four are right; what was wrong was the property
guarding them, and that is fixed.
