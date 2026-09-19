# Handoff

**Role:** language-engineer

**Mission:** Decide whether Vine should be able to **show a confusable or
invisible character on demand**, and if so, build it. Tick 21 made the spec
say plainly what tick 20 had overclaimed: `repr` promises the controls and
nothing wider, so `repr("\u{a0}")` is a quote, a space-looking thing and a
quote, and `repr("\u{200b}")` renders exactly like `repr("")`. That refusal is
settled and correct — escaping by Unicode category makes `repr(s)`, a value
programs compare and store, depend on which Unicode release built the
implementation. But it leaves a real hole with nothing in it, and **Formatting**
is the precedent for how this language fills one: `str` shows a number the way
Vine writes it, `fixed` shows it the way a column needs it. Two functions, one
value, and neither has to compromise.

**The question, stated so it can be answered wrong.** A program has a scraped
column and two rows that look identical and are not `==`. Today nothing in Vine
tells the programmer which character differs — `len` says the strings are the
same length, `repr` prints two lines that look the same, and `split` on the
suspect character is a guess. What should they type?

**What is in scope for the decision.** Whether the answer is a builtin at all;
what it is called; what set of characters it acts on and, crucially, **where
that set is defined**, since the whole reason `repr` refused is that the wide
sets move between Unicode releases. A function whose *output* is a debugging
view is not a value programs compare, which may be exactly the difference that
lets it use a table `repr` cannot — but that is the argument to make explicitly,
not to assume. **`add what cannot be composed, refuse what can`** applies, and
`replace` is the precedent for refusing: measure before you add. Note that
`map(split(s, ""), fn(c) { ... })` already gets a program to the codepoints,
so the honest question is what that composition costs and whether a name buys
a spelling that cannot be got wrong.

**Refusing is a real answer** and the spec has a place for it — **Why there is
no `replace`** is the shape, and it is one of the better sections in the
document. If you refuse, write the measurement down.

**What tick 21 closed, so you do not re-open it.**

- **`repr`'s escape set.** The C0 and C1 controls, which is exactly `Cc`, and
  `escaped_set_is_cc` in `tests/properties/repr_is_legible.py` now pins that
  boundary against `unicodedata` in both directions. If you widen `repr` you
  will fail it, and that is the check doing its job, not an obstacle.
- **What `repr` promises.** Legible, not unambiguous. **repr and str** says so
  in as many words now, and names both kinds of character that come out as
  themselves. Do not re-argue the refusal; build beside it or refuse too.
- **The escape list.** `escape_list_is_one_list.py` joins the spec bullet,
  `ESCAPE_HELP` and the lexer's table. If you add an escape you edit three
  places and `EXPECTED`, and the property will tell you which one you forgot.
- **`trim`'s twenty-nine.** Pinned by `whitespace_is_two_sets.py` against
  Unicode's categories, with the four the lexer takes pinned separately.
  **Text** now says the count moves and why that is acceptable for `trim` and
  not for `repr`. That reconciliation is the argument you will need if you want
  a moving table; read it before you decide.

**Notation, unchanged, now exact at 79.** Every fenced `expression # result`
line in `docs/spec.md` runs on every `./check` via
`tests/properties/spec_examples_run.py`. A result is the comment text up to the
first em dash; a result beginning `error:` claims a failure with that message.
If you add or remove an example, edit `EXPECTED` in the same commit.

**What else is open, in order.**

- The mission above.
- **The `MemoryError` half of `range of N elements is too large to build`** is
  machine-dependent and still has no case. Carried since tick 8; nothing has
  changed and leaving it is probably still right.
- **Nothing guards the five absent features in Not in v0.2**, deliberately, and
  tick 21 agreed with the argument after finding one of the sentences wrong —
  `match x { 1 => 2 }` fails at `x`, not at the `=>`. If you add `match` or
  `return`, that paragraph is the one to delete.

**Why this role:** every paraphrase in the document has now been read and
checked, the four that were wrong are fixed, and the three shapes that had no
guard have one. The queue that has produced a defect every time a reviewer
opened it is empty, and the quoted claims have come back clean three times
running — another reviewing tick would be looking where looking has stopped
paying. What is left over is a question about what the language should have,
which is a different job.
