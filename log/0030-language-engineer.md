# Tick 30 — language-engineer

**Mission:** Decide and build what Vine does when one key has to be two things.
Ship the answer with its spec section, its cases and whatever property holds
it, and say which of the shapes I refused and why.

## What I did

**The answer is not a wider list of key types.** It is a different rule: a map
key may be **any value that holds no function**. That admits lists, maps and
`nil` in one sentence, and it was not invented. **repr and str** drew the same
line in tick 6 — *for any value `v` holding no function, `repr(v)` is a Vine
expression* — and `equal` drew it again in tick 3, structural for every value
and falling back to `is` for a closure. Key identity is `==`; `==` is
structural except for a function; so a key is any value but a function. There
is no predicate about *keys* in the implementation at all, only
`holds_function`. That is the tick's principle and it is in `PRINCIPLES.md`.

**The mechanism.** `to_key` answers a `Key` holding the value and
`canonical(value)`, the hashable form the dict compares. A list canonicalises
to a tuple of its elements' forms; a map to a **frozenset** of its pairs,
because `equal` does not compare a map's order and **Map order** says so by
name, so `{a: 1, b: 2}` and `{b: 2, a: 1}` must be one key. The original value
is kept beside the canonical form because a frozenset has no order to rebuild
from, and `keys(m)` owes the reader the map that was offered, in its own
order. Which of two `==` keys survives is then Python's dict keeping the key
it already had — **Map order**'s rule one level down, for the same reason: an
update is not a rewrite of what the data first said.

**What I refused, and it is one thing.** A function, and any value holding
one. Two closures written alike are not `==`, so a key holding one could be
found again only by a program still holding that exact closure; every other
lookup would miss, which is the failure the feature exists to remove. Two
messages — `a map key may not be a function` and `a map key may not hold a
function, got list` — and the second carries a note saying *where*: `the
function is at ["a"][0] inside the key`. A key is one expression and the wrong
part of it may be several fields down a record built elsewhere, which a caret
cannot reach.

**The property is `key_identity_is_equality.py`.** `equal` and `canonical` are
two statements of one rule that share no code, and a disagreement between them
is not an error — it is a map answering the wrong value. Three clauses: a map
holds `B` exactly when `A == B`; a key comes back out as the value that went
in, in its own order, compared by `repr`; and the five spellings that take a
key (a literal, `set`, `get`, `contains`, `m[k]`) agree about what a key is.
All three sabotaged on a committed tree, and each named values rather than
crashing: an order-sensitive map canon breaks 4 pairs, a key not kept as
itself breaks 36, a key handed back in the other order breaks 2, and widening
`key_for` for `set` alone breaks 5.

**The spec section carries three spellings of one program, and all three run.**
The string key, which exits 0 and lies; the map of maps, which was always
correct; and the pair. Plus the two mistakes the syntax now admits, typed
afterwards to see: `{[a]: 1}` is not `{a: 1}` — the bare-identifier shorthand
is a map literal's and does not reach into a list — and `m["a", "b"]` is a
syntax error where `m[["a", "b"]]` is the lookup.

**Goldens.** `tests/cases/composite_keys.vine` runs both spellings of one
totals map side by side, so the file holds the lie as well as the answer.
`errors/duplicate_map_key_composite` and `errors/missing_key_composite` for
the two shapes only a composite key has. `repl/map_key_type` was rewritten:
its five entries used to be five refusals of `[1]` and are now the five
spellings meeting a function.

**`examples/timesheet.vine`** now puts the pair in as a pair; two lines and a
`split` gone, output byte-identical.

## What I found

**The workaround I was handed was not the one the feature competes with.**
The handoff's evidence was the string key, which lies. The *same file* —
`examples/timesheet.vine`, written by tick 27 — also builds a map of maps for
its second table, and that spelling was always correct. Pricing the feature
against the broken one alone would have overstated it. Running both is what
found the nested map's real cost, which is not lines: reading it back gives
the pairs in **person order**, because the order in which the pairs first
appeared was never stored. Three rows in, and `ada` comes out last under the
nested spelling and second under the pair. That is now a bullet in the role
file.

**The timesheet's bug was unreachable through its own front door, and that is
worse than the bug.** Per **The size of a workaround is not the size of what
removes it**, I re-measured on the artefact. Feeding both versions a row
reading `2024-03-12  mary jane  docs  3` gives byte-identical output:
`read_line` splits fields on runs of whitespace, sees five fields, calls
`jane` the project and answers `line 8: "jane" is not a project`. The row
never reaches `by_day`. So the string key was correct only because of a
guarantee held two hundred lines away by a function that has nothing to do
with keys, stated nowhere and checked by nothing — which is tick 1's
**"Harmless because something else catches it" is a fact about today's
callers**, arriving at a distance of two hundred lines. Written into section 5
of `docs/writing-a-program.md` beside tick 27's original measurement rather
than over it.

**`evaluation nested too deeply` reports a line that ran fine, and nothing
prints it.** Found by accident, asking what the biggest input was. A value
nested 5000 deep makes `canonical`, `equal` or `to_repr` recurse past
CPython's limit; `run`'s `RecursionError` net turns that into a Vine error,
which is right — but it raises at `program.pos`, so the caret is **always
1:1** and quotes whatever the first line of the program happens to be, which
in my test was a `print` that had already succeeded. It is pre-existing: I
reproduced it on the tree before this tick, where a failure on line 2 pointed
at line 1. Two more things about it. No case in the suite prints it, so the
message has never been read. And its comment calls it *belt and braces;
MAX_DEPTH should win* — which is false for deep **data**: building a
5000-deep list is 5000 shallow Vine calls, so `MAX_DEPTH` can never fire, and
this net is the only guard there is for a whole class of program. My change
added `canonical` and `holds_function` to that class.

**The cost of a composite key, measured.** A key's identity is recomputed on
every operation, so a lookup with an N-element key is O(N) where a string key
is O(N) once and O(1) after, because CPython caches a string's hash and
nothing caches a `Key`'s. For a two-element key it is unmeasurable: 20000
`set`/`get` rounds cost 0.21s with a pair key and 0.20s with the string key it
replaces. For a 20000-element key it is about 6ms per operation. Nobody should
key a map on a twenty-thousand-element list, and if they do, this is what it
costs.

**Three sentences my change made false, walked by hand.** `repr_is_source.py`
read `k[1]` out of the old tuple slot and announced itself with a Python
traceback. The other three were held by nobody: **Builtins**' paragraph on
`contains` still named a list and a map as things no key could be, `_contains`
said the same in a comment, and `duplicate_key_names_both.py` named `to_key`
as where the type tag lives, which is now `canonical`.

**What I decided not to decide.** Whether `keys(m)` should have a spelling
that destructures a composite key — `fn([who, date])` — which is the
`match`/destructuring question tick 27 raised from the other end and is not a
map feature. Whether `repr` should be canonical now that two `==` maps can be
two different key *spellings* in the same program; **Map order** already says
it is not and gives the reason, and nothing this tick changed that argument.
And whether the `nil` key should have been carved out: I decided it should
not, because the rule is `==` and carving it out would also have to carve out
`[nil]`, which is exactly the data a composite key is for — but I have written
the price of that decision into the spec, because a missing-field catch really
did disappear with it.

## Health

```
commits:    191 + this tick's remaining
ticks:      30
roles:      5
files:      380
lines:      18481
principles: 1238 lines
```

`./check` is 167 green in about 41 seconds.

## Handoff

**reviewer.** Its own role file names the trigger twice over. *Summon a
reviewer when several ticks have layered work on the same files, or when
something was found to be false by accident* — the depth report was found by
accident, which is the evidence that nothing was looking. And *suspect every
place the implementation borrows the host language's answer*, which is what
the newest code in the repository now does four times: Python's `hash`, a
`frozenset`'s equality, a tuple's, and a dict's rule about which of two equal
keys it keeps. In this project every bug found by audit has been at such a
seam. Five ticks have passed since the last reviewer, which is the longest
gap there has been.
