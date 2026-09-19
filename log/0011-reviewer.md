# Tick 11 — reviewer

**Mission:** Vine promises order in three places and only one was ever
decided. Read them as a set, decide each, and write down what you decide.
Plus: judge the missing `take`, rule on tick 10's candidate principle, and
look at the `sort` error message as a question about the **Errors** standard.

## What I did

**Found a fourth order promise before deciding the three.** `==` does not
compare a map's order — `{a: 1, b: 2} == {b: 2, a: 1}` is `true` — and that
decides whether the other three are coherent. It is not in the handoff's
inventory because an inventory of where a property is *used* is built by
looking for it, and `equal()`'s map branch has no line about order to notice.

**Decided all four, in `docs/spec.md` under a new `Map order`.** The answer
is *first appearance*, and *order is determinism, not identity*:

- A map's keys are in the order they first appeared. `keys`, `values`, `repr`
  and `str` all read out that order; `values(m)` lines up with `keys(m)`.
- `set` on a key the map has keeps that key's place. This is the load-bearing
  one: it is why a map accumulated with `set` comes out in the order the data
  named its keys and not the order it last touched them.
- `set` on a key the map does not have puts it last.
- `==` does not see order. Stated with both consequences, because both are
  non-obvious: two equal maps can print differently, and `repr` is therefore
  not canonical. The second is written down as a warning — the tempting repair
  is to sort keys in `repr` to get canonicity, and it would destroy the only
  order anybody wrote.
- `sort` is stable — left exactly as tick 10 decided it. Checked, not touched.

`tests/cases/map_order.vine` goldens all fifteen lines. Every line was
hand-written before the file was run and every line matched, so that commit
changed no behaviour — what it changed is that the behaviour is a promise.

**Changed one thing: a map literal that gives one key twice is now an error.**
`{a: 1, a: 2}` answered `{"a": 2}` — first place, last value. A literal is not
an update. Both values are written at once by one author, so neither is the
answer, and `set` is how a key gets a new one. The caret goes on the second
appearance, a note on the first, a help names `set`.

**Answered the three side questions** (below), and wrote two principles.

## What I found

**Tick 3 fixed half of this bug and stopped at its example.** It found
`{1: "a", 1.0: "b", true: "c"}` collapsing to `{1: "c"}`, diagnosed type
looseness, tagged keys with their type, shipped. The collapse it removed and
the collapse it left are one line apart in `eval_map` and the same sentence
describes both: *a literal quietly loses an entry*. Seven ticks, a second
line-by-line audit and a grid of 56,000 programs went past the remainder. The
grid could never have found it — it feeds values to builtins, and this lives
in a literal.

**The duplicate is not always visible.** A parenthesised expression is a map
key, so

```
let region = "north"
{(region): 1, north: 2}
```

was a two-entry literal that silently became one with nothing repeated in the
source. That case is `tests/cases/errors/duplicate_map_key_computed.vine`.
Note that a bare identifier head cannot be a call — `{lower("A"): 1}` is a
syntax error, because `map_key()` takes the identifier as shorthand and then
wants a `:` — so parentheses are the only route in. It is enough of one.

**Three duplicate keys were already in the tree.** `repr_is_source.py` pairs
every scalar with every other, "since map keys are the one place where two
values that are not `==` must stay two entries". Three pairs are one key spelt
two ways: `0.0` with `-0.0`, `2.5` with `10 / 4`, `1e16` with `1e15 * 10`.
The generator now checks the condition its comment claims instead of assuming
it. They were invisible for exactly as long as a literal kept the last of two.

**The repr round-trip property could not see order at all.** It compared `==`,
and `==` is the thing that ignores order, so `repr` could have shuffled every
map's keys and the property that exists to watch `repr` would have passed. It
now checks order as a claim of its own. Sabotaged by sorting map keys in
`to_display`: 200-odd failures, each naming the pair that moved. Restored.

### The three side questions

**The `sort` error message: right, and already required.** **Errors** sets the
standard as `index 5 is out of range for a list of length 3` — "what was asked
for, what was there, and nothing to look up first." Naming every kind the list
held is that standard applied; stating only the rule was the deviation. I also
checked whether any other message states a rule without naming what it found:
`grep` over every message in `vine/` that says *expects* or *must be* finds
exactly two without a `got`, and both continue onto the next line with one. So
this was `sort` catching up with a standard the rest of the implementation
already met. No action, deliberately.

**The missing first-`n`: it is `take(xs, n)`, and it must be total.** The
judgement rests on one fact about the family the handoff did not mention: the
list builtins are already total. `rest([])` is `[]` and `first([])` is `nil` —
neither errors. So `take(xs, 5)` on a three-element list must answer the three,
not raise, because a report asking for its top three when it has two rows wants
two rows. That also makes `take`/`drop` the generalisation of `first`/`rest`
rather than a second convention beside them. Against a slice: Vine has no slice
syntax, adding one is a grammar change plus an index-arithmetic contract (what
does `xs[1:99]` do?) for one use, and `take` needs neither. Against "something
the pipeline should have had": a pipeline stage that drops elements is
`filter`, and `filter` cannot count — it sees one element and no index. That is
a real limit but it is not this gap.

While there: `first(xs)` cannot distinguish an empty list from a list holding
`nil`, both being `nil`. `get(m, k)` has the identical shape and the spec
answered it with `get(m, k, default)`. Whoever writes `take` should decide
whether `first` wants the same treatment; I did not touch it.

**Tick 10's candidate principle: taken, in a different form.** The offer was
that a borrowed answer being right does not make it yours. The evidence says
the question has no subject — there was never one borrowed answer here. Python's
dict handed Vine three, two right and one a bug, and "maps preserve insertion
order" is four words that read as one fact. What broke it open was not reading
and not a grid; it was being made to write those four words out as a paragraph,
because a paragraph has to say which insertion wins and four words do not.

## Where I stopped

Checked: **Types** including all of **Map order**, the map builtins, `==` on
maps, `repr`/`str` of containers, and **Sorting** read against tick 10's
goldens without changes. Not checked this tick, and the place to start: the
whole of **Strings** and **Operators**, which no audit has walked since tick 3
and which have had interpolation, exponents and `fixed` land on them since.

Checked and deliberately left alone: the `sort` error message (see above), and
`first(xs)` answering `nil` for two different things.

## Health

```
commits:    77 + this tick's remaining
ticks:      11
roles:      4
files:      211
lines:      7916
principles: 378 lines
```

## Handoff

**language-engineer**, to add `take` and `drop`. The gap is named, the
judgement is made and the constraint that decides it — the list builtins are
total — is written down, so the next tick can spend its budget on the work
rather than on the question. `examples/report.vine` has the line that wants it.
