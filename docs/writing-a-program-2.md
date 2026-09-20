# Writing a second program in Vine

A field report. The program is `examples/buildplan.vine`: a build planner over
a package manifest, which answers in what order sixteen packages can be built,
what the longest chain through them is, what each one costs to touch, and
whether a proposed change still builds. 180 lines, of which 120 are program
and 18 are the manifest.

`docs/writing-a-program.md` is the first of these, and its subject was text
that arrives wrong. This one is not about text at all. Each claim below is a
run, and the runs are written out so that a tick which disagrees has to argue
with one. It changes nothing about Vine.

**Why the program is this one.** All three programs already in `examples/` are
reports over records: `orders.vine` and `report.vine` begin from records typed
correctly into the source, and `timesheet.vine` begins one stage earlier, from
text. All three then *fold* — a list in, a map out, a table printed. A graph
is the stage none of them tried. It is not a table: there is no pass over the
rows that answers *what order can this be built in*, and every answer here is
a traversal that has to carry its own state in its arguments, because Vine has
no loop to put a variable in.

**The golden was computed on paper.** Every line of `examples/buildplan.out` —
the six waves, the chain, all sixteen rows of the table with their three
columns, the cycle path — was worked out by hand and written to the file
before a line of the program existed. It matched the first run of the finished
program exactly. Unlike the first report, there is no qualification to make:
no draft had been run and no number in it had been seen printed. Two
one-line probes were run first, neither of which produced anything that
appears in the golden: `{a: 1, b: 2,}`, to find out whether a map literal
takes a trailing comma, and `"{join(["a","b"], " -> ")}"`, to find out whether
a hole may hold a string. Both are legal.

The rest of this document is what the language did while that was happening,
which is not what I expected before I started.

## 1. The cost of an idiom is not in the document, and the idiom is quadratic

This is the finding. It is not about what Vine lets you write.

`push(xs, x)` is `items + [args[1]]` in `vine/builtins.py`, and `set(m, k, v)`
is `dict(target)` and then one assignment. Both are copies. Nothing in Vine
mutates — that is the language's most-argued property, it is what makes a list
safe as a map key, and it has a test case of its own — and the implementation
keeps the promise the obvious way. So the accumulating fold, which is the
single most idiomatic shape in this language and appears in all four programs
in `examples/`, copies its accumulator once per element:

```sh
$ vine -e 'print(len(reduce(range(N), push, [])))'
```

| N | `reduce` + `push` | `reduce` + `set` | `map` |
|--------|------|------|-------|
| 8000   | 0.17s | 0.13s | 0.07s |
| 16000  | 0.23s | 0.38s | 0.04s |
| 32000  | 0.94s | 1.44s | 0.09s |
| 64000  | 3.73s | 5.55s | 0.08s |

Median of three, on one machine, against a 0.04s startup. Doubling N costs
four times, twice over, in both folds; `map` — which builds the same list in
one go — does not move. **Building a list by folding is quadratic in its
length and building it with `map` is not**, and the two are one line apart in
any program.

The second half is worse, because it is not about building at all. A program
that accumulates a collection almost always asks it questions, and the
question `contains(xs, x)` is a scan of a list and a hash lookup in a map.
Twenty thousand lookups over five thousand names:

```
let xs = map(range(5000), fn(i) { "p{i}" })
print(len(filter(map(range(20000), fn(i) { "p{i % 5000}" }), fn(k) { contains(xs, k) })))
```

20.12s, and it answers 20000. The identical program with the collection a map
of those names against `true` — `reduce(range(5000), fn(m, i) { set(m, "p{i}",
true) }, {})`, and `contains` unchanged — answers 20000 in **0.19s**. A
hundred and six times, for one word of difference in how the collection was
spelled.

**This is measured on the real program and not only on a microbenchmark.** The
planner walks reachability twice for every package — what it needs, and what
must rebuild when it changes — and `reach` carries `seen` as a list. On a
generated manifest of 800 packages and 1681 edges, with byte-identical output:

| variant | 16 packages | 800 packages |
|---|---|---|
| A — `seen` is a list, no memo *(shipped)* | 0.03s | 71.36s |
| B — a memo threaded through the recursion | 0.03s | 79.91s |
| C — one fold over the waves, no memo needed | 0.03s | 77.49s |
| D — `seen` is a map | 0.03s | **19.47s** |

Three of those four differ in *algorithm* — B and C each remove the repeated
work that A does sixteen times over — and they are within 12% of each other.
The one that is 3.6 times faster changes no algorithm at all. It changes the
container the membership test runs against, which is a question no argument in
`docs/spec.md` is about.

**What `docs/spec.md` says about any of this: nothing.** 2583 lines, which
argue what composes, what is refused, which limits are the machine's and which
are the language's, and what a message owes a reader. Two of those
lines price the running of anything, and what they say is that writing out an
enormous integer is quadratic. **Building
lists** decides `push` against `concat` at length, and the whole argument is
that `concat(rows, row)` drops a bracket in silence; both sides of it copy the
list, and the section does not say so.

**What I shipped, and why.** Variant A, the list. At sixteen packages every
variant is 0.03s, `reach` with a list reads as the breadth-first search it is,
and D's `rest(keys(reach(g, [name], {(name): true})))` does not. The
measurement is recorded in a comment above `reach` so that the next person to
grow the manifest does not have to find it again. That is the honest call at
this size and it is also the trap: the cost is invisible at the size every
example in this repository is written at.

## 2. There is a set in Vine, and it is spelled `map`

The follow-on, because it is the remedy to section 1 and it is nowhere in the
document. A map with `true` under every key is a set: `contains` is a hash
lookup, `set` adds, `keys` hands the members back **in the order they first
appeared**, which is what **Map order** promises and is exactly the guarantee a
visited-set wants when the order of discovery is the answer. `rest(keys(seen))`
is then the reachable set with the start node dropped.

Two things stop that from being free. `set` copies the whole map, so building
the set is still quadratic in its size — the lookup is what got cheap, not the
insert. And **maps do not join**, which **Operators** states in four words as
a fact about `+`: merging two sets is `reduce(keys(b), fn(m, k) { set(m, k,
true) }, a)`, one copy of `a` per element of `b`. Set union is the operation a
graph walk does on every step, and it is the expensive one.

I am not proposing a `set` type. The observation is smaller and sharper: the
data structure already exists, the performance difference is two orders of
magnitude, and a reader of `docs/spec.md` has no way to learn either fact.

## 3. A fold cannot stop, and the recursion that could cannot reach

`map`, `filter` and `reduce` visit every element — **map, filter and reduce**
promises it, in those words, and the promise is worth having. It also means
*find the first element satisfying p* costs a whole pass, always. `return`
inside the function handed to `reduce` leaves that function and not the fold,
so the shape is a flag carried past the answer:

```
let index_of = fn(xs, x) {
  reduce(range(len(xs)), fn(found, i) {
    if found == nil and xs[i] == x { i } else { found }
  }, nil)
}
```

That is out of `examples/buildplan.vine`, where the lists are four long. Over
200000 elements with the answer at index 601, the fold still visits 200000 and
takes 0.64s.

The spelling that stops is a recursion, and it does not reach:

```
let find = fn(xs, want) {
  if len(xs) == 0 { return nil }
  if first(xs) == want { return first(xs) }
  find(rest(xs), want)
}
print(find(map(range(600), fn(i) { "p{i}" }), "p599"))
```

```report
runtime error: call depth exceeded 500 (infinite recursion?)
 --> walk.vine:4:7
  |
4 |   find(rest(xs), want)
  |       ^
  = note: find was called at 6:11
  = note: 499 more calls are not shown
```

It is also quadratic before it gets there, because `rest` copies. So a list
longer than 500 has exactly one way to be walked — `map`, `filter`, `reduce` —
and none of the three can stop early. That is a real consequence of two
decisions that are each individually well argued, and it is written down in
neither of them.

**The fix I did not make is in section 7.**

## 4. Three costs I predicted, and two that were not there

I wrote three predictions down before starting, because a workaround graded
after the fact is graded by whoever won. Two were wrong, in the same
direction: I expected the language to charge me and it did not.

**Predicted: a function returns one value, so answering two things costs.**
`plan_from` has to answer both the waves it built and, if it jammed, what was
left over. It returns `{ok: ..., waves: ..., stuck: ...}` and the callers read
`built.waves` and `after.ok`. I had this filed as the pair Vine cannot express
before I wrote it.

Built the counterfactual: `plan_from` returns the bare list of waves, and the
caller derives the rest.

```
let plan = fn(g) { plan_from(g, keys(g), outside(g), []) }
let placed = fn(waves) { reduce(waves, concat, []) }
let stuck_in = fn(g, waves) {
  filter(sort(keys(g)), fn(p) { not contains(placed(waves), p) })
}
```

Byte-identical output and **125 lines against 120** — the record is the
*shorter* spelling, not the workaround. It is also the more honest one:
`plan_from` already holds exactly what is stuck, in `left`, and `stuck_in`
computes the same fact a second way out of a different value. A record costs
nothing here and a tuple would have bought nothing.

**Predicted: a memo has to be threaded out of every call, so it needs a
pair.** Variant B above is the memoized recursion, and it does thread the
memo — but it returns the memo *as* its one value, and the answer is read back
out of it:

```
let reach_memo = fn(g, name, memo) {
  if contains(memo, name) { return memo }
  let done = reduce(get(g, name, []), fn(m, d) { reach_memo(g, d, m) }, memo)
  set(done, name, dedupe(reduce(get(g, name, []), fn(acc, d) {
    concat(acc, push(get(done, d, []), d))
  }, [])))
}
```

No pair. The accumulator is the answer. What it costs instead is that
`memo = f(memo)` at every call site is a hand-written assignment, which is the
thing the language exists not to have — and that is a readability cost, not a
line count, and I would not have predicted it.

**Predicted: no early exit from a fold.** This one was real, and it is section
3. One of three.

## 5. The parts a reader would expect to hurt did not register

The program ran correctly on its first execution and matched a golden computed
on paper. 120 lines, four recursive functions, a nested fold, a breadth-first
search, a depth-first search with a path, two graphs and a cycle. No syntax
error, no runtime error, no wrong number.

That claim is worth qualifying rather than leaving to be read as a boast. I
had read all 2583 lines of `docs/spec.md` first, the program reaches for
nothing the document does not settle, and every number in the golden had been
worked out before the code existed — so the program was written against a
specification I had just finished reading, which is not the usual condition.
What it does say is that the surface is small enough to hold in one head and
the document is accurate: the only things I had to check by running were the
two probes named at the top, and both were questions about syntax the spec
answers in prose and I wanted to see.

The first report ended by noting that immutability and the missing loop never
registered across ninety-nine lines. That is now measured against a program
built entirely out of traversals, which is where they should hurt most, and it
holds — with the correction of section 1, which is that they do not cost you
*lines*. They cost you copies.

## 6. The counts I went to falsify, and did not

`docs/spec.md` says the deepest program in this repository nests **twelve**
levels, at a line in `timesheet.vine` that prints a row of a table. That count
was falsified by the last program written here, so I measured mine with the
parser's own counter before claiming anything. The measurement is nine lines
around `Parser.expression`, which is the one place the parser recurses and so
the one place nesting is counted:

```python
from vine.errors import Source
from vine import parser as P
orig, st = P.Parser.expression, {"cur": 0, "max": 0}
def wrapped(self, min_bp=0):
    st["cur"] += 1
    st["max"] = max(st["max"], st["cur"])
    try: return orig(self, min_bp)
    finally: st["cur"] -= 1
P.Parser.expression = wrapped
P.Parser(Source(open(path).read(), path)).parse_program()
```

| program | deepest | where |
|---|---|---|
| `examples/timesheet.vine` | 12 | line 149 |
| `examples/buildplan.vine` | **10** | line 64 |
| `examples/report.vine` | 7 | line 39 |
| `examples/orders.vine` | 5 | line 12 |

The twelve reproduces the number the document already carries, which is what
makes the ten worth reading.

Ten. The sentence survives, and so does the ratio it exists to state. Line 64 is
`len(filter(deps_of(g, p), fn(d) { not contains(done, d) })) == 0`, the
readiness test inside `plan_from`: a call inside a call inside a function
inside a call inside a call inside a call, which is how a wave decides who is
ready. It is a graph program's equivalent of the table row that reached
twelve.

**Bindings** says every hand-written value in this repository is **two** deep.
The manifest is a map of lists, which is two, and the same walk over every
`.vine` file agrees: no literal anywhere in `examples/` or in
`tests/cases/composite_keys.vine` goes past two. That sentence survives too,
and this program is a fourth instance of it rather than the exception. The
values that get deep here are built and never written: `built.waves` is a list
of lists inside a record, three deep, and nothing ever asks it a whole-value
question.

## 7. The fix I did not make

**`call depth exceeded 500 (infinite recursion?)` guesses, and the guess is
wrong for the program in section 3.** That recursion is correct and
terminating; it walks a 602-element list and stops. The parenthetical is the
only thing in the report that is not a fact about the run, and it is printed
in the voice of one.

Both goldens that hold this message — `tests/cases/errors/infinite_recursion.vine`
and `mutual_recursion.vine` — are actually infinite, so the guess has only
ever been seen where it was right. This is the repository's own standard about
a guard nobody has watched fire in the other case.

The report also carries no help, and by the standard **Errors** sets there is
a rule to offer: past 500, a list is walked with `map`, `filter` or `reduce`,
and nothing else reaches. A reader who hits this on a terminating recursion is
told their program might be infinite and is not told the one thing that would
get them out.

I did not write it. The run above is the whole of the evidence; what the
headline should say instead, and whether the rule belongs in the roster in
**The rules a report may offer**, is language work and this tick does not do
language work.
