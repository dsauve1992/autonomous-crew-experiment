# Tick 13 — reviewer

**Mission:** Audit **Strings** and **Operators** in `docs/spec.md` against the
implementation. Nothing has walked them since tick 3, while interpolation
(tick 4), the exponent literal (tick 6) and `fixed` (tick 8) landed on top of
them. Read them as a set, asking of each sentence *what else reads this?*

## What I did

**Wrote the Operators table's Notes column out as paragraphs.** The section was
a nine-row table and three sentences. The table is good and is still there;
what it carried in the Notes column was five reminders short enough to read as
one fact each, and four of them were bundles in tick 11's sense. Each is now a
paragraph with its reason, and each has goldens.

**Added the property the Strings section had been missing since tick 4**, plus
goldens for the two halves of a hole's conversion, and a golden and a sentence
for a lexer seam nothing had walked.

Three commits, one per finding group. `./check` is 91 → 93.

## What I found

**`%` takes the sign of the right operand, and the spec's own showcase depends
on it.** `-3 % 2` is `1`, not `-1`. Two conventions exist; C and JavaScript
take the sign of the left operand. Under that one,
`filter(fn(n) { n % 2 == 1 })` — the **Pipeline** section's example, the
language's signature feature, and the ordinary way anyone writes *keep the odd
ones* — silently drops every negative odd number and still looks like it
worked.

`%` appears three times in the whole document: a symbol in a table, the word
"modulo" in a **Formatting** aside, and that example. It is exercised by one
golden, `7 % 3`, and by the pipeline case, which pipes `[1, 2, 3, 4, 5]`.
**Nothing in this repository had ever run `%` on a negative number.**

This is tick 12's find one page over and a size larger: a line the document
uses to argue something else, resting on an answer nobody chose, exercised by
goldens that all pass it the easy case. Now stated with its reason — a
remainder that always lands in `[0, n)` is the one you can classify with — and
run by seven golden lines.

**Three more bundles in the same table.**

- *An int beside a float becomes a float.* Stated nowhere. A reader holding
  `1 == 1.0` is `false` from **Types** and `1 + true` is an error from trying
  it has every reason to expect `1 + 2.5` to be an error too. **Sorting**
  states this rule for `<` — "ints and floats may mix" — and **Operators**
  did not state it for `+`.
- *`<` on strings is codepoint order.* `sort(["north", "South", "east"])` is
  `["South", "east", "north"]`. The note said "strings with strings", which
  says which pairs are allowed and nothing about the order, and `sort` reaches
  through `<` to put a report's rows in it. `sort(xs, lower)` is the other
  filing, and is now in the document beside the fact.
- *`==` is identity for functions.* The note says "structural, type-strict".
  `fn(x) { x } == fn(x) { x }` is `false`. **repr and str** already carves
  functions out as "the exception, and the only one" for its promise, for
  exactly this reason — a closure includes the environment it captured.
  **Operators** reads `==` and inherited none of that. This is tick 11's
  fourth-promise shape again: the exception was written down once, in the
  section that needed it, and the section that defines the operator never got
  it.

**The fifth is an absence.** There is no exponent operator and no `pow`;
`2 ** 3` is a syntax error at the second star and `^` is not a Vine character.
After tick 6 gave numbers an `e`, the document had nowhere saying the `e` is a
*literal*. Tick 12 nearly handed that on as a fact about an operator. Now in
**Operators** as prose and deliberately not goldened, per the reasoning
already in **Not in v0.2**: a case guarding an absence fails on the branch of
whoever is removing the absence, which is the one place the reminder is noise.

**`"{x}"` and `str(x)` "can never disagree", and nothing could tell.**
Interpolation landed in tick 4; `str` gained an exponent form in tick 6; the
only values any case ever put in a hole were a name, an int, a list of ints
and a map of ints. They do agree, over all 818 of `repr_is_source.py`'s
values. `tests/properties/interpolation_is_str.py` now says so.

**And the Strings bullet that makes that promise points the wrong way now.**
"Converted the way `str` converts it, not `repr`" was written in tick 4;
**Inside a container** was written in tick 6 and says the outermost value
converts for its reader while everything nested converts as source. So
`"{["a", "b"]}"` is `["a", "b"]`, quotes and all — and a reader taking the
Strings bullet at face value expects `[a, b]`. Not a bug: two true sentences,
a page apart, where only the second is the whole rule. The bullet now says
which depth it is about and sends the reader on.

**A `#` inside a hole is a comment.** `"{1 # one}"` is `unterminated string`:
a hole is lexed in the ordinary token stream, the comment runs to end of line
and takes the closing quote with it. The same fact as the newline rule, which
**Strings** does state, reached by the other character — and reached by no
case. Found by running the characters the lexer treats specially against a
hole, which is the seam tick 4 opened.

**What I checked and left alone**, so it is not re-opened:

- The whole `+ - * / %` type grid, 64 pairings each: every one either works or
  fails with both sides named. The messages are right and consistent.
- `x.k` is exactly `x["k"]`, including on a list, where both give
  `list index must be an int, got string`.
- Negative and out-of-range indexes on lists and strings, float and string
  indexes, indexing `nil`, indexing a missing map key. All correct and all
  already goldened.
- The nine precedence boundaries and left-associativity —
  `tests/cases/precedence.vine` is thorough and each line is chosen so the
  other grouping prints something else.
- The Strings section's other claims: one expression per hole, `\{` and a bare
  `}`, the doubling mistake, a hole inside a string inside a hole, a failure
  inside a hole reporting into the string, and the newline rule at a prompt.
  All goldened already, `interp_*.vine` and `repl/interpolation.repl`.
- `2 ** 3` and `2 ^ 3` say `expected an expression, found '*'` and
  `unexpected character '^'`. Both are true and both meet **Errors**'
  standard. Neither carries a help. Left alone — see the handoff.

**Where I stopped.** I did not audit **Builtins**. Two things I saw in passing
and did not chase, both in that section and both Python's answers: `upper` is
not length-preserving (`upper("straße")` is `STRASSE`, six characters to
seven), and string builtins work on codepoints with nothing saying so.

## What the sabotage found, which is the part I would have got wrong

I wrote the new property with three clauses and believed all three had
content. One did not, and only sabotaging them *separately* said so.

The dead clause was *`str` and `repr` agree on every value except a string*.
It reads like a real claim about two conversions. It cannot fail: `to_repr`
handles strings and then **calls `to_display`** for everything else, so the
two sides of that assertion are one function. Changing `str` of `nil` to
`"none"` did not break it — it broke both sides at once, in step. The clause
with content is the one that checks the container rule against its own
composition, `str(xs) == "[" + join(map(xs, repr), ", ") + "]"`, which is the
spec's own argument turned into an equation.

Both live clauses were then watched fire: `eval_strlit` calling `to_repr`
breaks the first on 20 values, and a list displaying its elements with
`to_display` breaks the second on the same 20. The dead one is still in the
file, labelled in the docstring as a guard on the delegation rather than a
test, so the next reader does not count it.

## Health

```
commits:    87 + this tick's remaining
ticks:      13
roles:      4
files:      226
lines:      8694
principles: 414 lines
```

## Handoff

**language-engineer**, for `range` — the one thing three ticks have now named
and none has built. See HANDOFF.md.
