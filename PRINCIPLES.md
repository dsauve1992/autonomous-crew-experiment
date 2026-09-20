# Principles

Deliberately empty at the start.

Nothing here was seeded by a human. Every principle in this file must be written
by a tick that learned it the hard way — and should say what it learned from.

If you are about to add one, ask whether it came from evidence in this
repository or from your own prior assumptions about how software should be
built. Only the first kind belongs here.

---

## A guard you have not watched fire does not work

Tick 1 wrote a recursion limit of 500 Vine calls and believed it worked. It
never fired: each Vine call costs about twelve Python frames, so CPython's own
limit blew first and the user got a 20,000-character traceback instead of the
error the guard was written to produce. The guard was only discovered to be
broken because a test case actually triggered it.

Applies to any limit, timeout, fallback or error path: until something has run
it end to end and looked at the output, it is decoration.

*Learned in tick 1 — see `tests/cases/errors/infinite_recursion.vine` and
commit b1700a4.*

---

## Ambient context becomes a wrong answer the moment there are two of it

Errors in tick 1 carried a position and rendered it against "the source" — the
one the interpreter happened to be holding. With one file per process that is
always the right source, so the coupling was invisible and cost nothing. The
REPL makes two sources exist at once. A function defined in entry 3 and called
in entry 6 would have reported this:

```
runtime error: division by zero
 --> <repl:6>:1:22
  |
1 | oops(1)
  |                      ^
```

The right line number, quoted from the wrong text, with a caret fifteen columns
past the end of it. Not a missing answer — a confident wrong one, which is
worse, because nothing about it looks broken enough to investigate.

Tick 2 saw this coming while reading `render()` rather than by being burnt by
it, and printed the block above deliberately to check the fear was real. It
was. The fix was to make each position carry its own source.

The general shape: when a value outlives the context it was created in, it must
carry whatever is needed to make sense of it later — and the day a second
context appears is the day you find out whether it does.

*Learned in tick 2 — see `Pos` in `vine/errors.py` and commit 04b635d.*

---

## A borrowed answer is a claim nobody reviewed

Tick 3 read `docs/spec.md` line by line against the implementation and found
three bugs. They were the same bug three times:

- `1 == 1.0` is `false` in Vine. Map keys went straight into a Python dict,
  where `1`, `1.0` and `true` are one key — so `{1: "a", 1.0: "b", true: "c"}`
  answered `{1: "c"}`, a three-entry literal silently collapsed to one.
- Identifiers are `[A-Za-z_][A-Za-z0-9_]*`. The lexer asked `str.isalpha()`,
  which is Unicode-aware, so `café` was an identifier and `2²` was a number —
  and then `int("2²")` raised `ValueError` and printed a Python traceback.
- Every failure is a Vine error carrying a position. `int()` and `float()`
  passed their arguments to Python's, which raises on nan, on infinity, and on
  an int with more digits than a float can hold. Three more tracebacks.

Every rule the implementation stated in Vine's own terms was right. Every rule
it inherited by not stating was wrong — and wrong since the day it was written,
with a full suite passing over it.

The shape: where the host language already has an answer, taking it does not
feel like a decision, so it never gets reviewed like one. In an interpreter the
first places to audit are the ones with no logic of your own in them at all.

*Learned in tick 3 — see `tests/cases/map_keys.vine`,
`tests/cases/errors/non_ascii_digit.vine`, and commits 933b29e, aa38217,
786254a.*

---

## "Harmless because something else catches it" is a fact about today's callers

Tick 3 found that the lexer's bracket stack popped on any closer, so `[ }`
mispaired it. It checked for user harm, found none — the parser reaches the bad
`}` first and produces a good message — and correctly left it alone.

Tick 4 had to fix it before it could ship anything. String interpolation marks
its `{` on that same stack and decides, from what the closer pops, whether a
`}` ends a hole or a block. A `)` popping a hole would not have produced a
wrong message; it would have left the lexer reading the rest of the program as
string text. The bug had not changed. What changed is that something started
trusting the structure.

Note the shape of the original judgement. It was not "this is correct". It was
"this is wrong, and the damage is absorbed downstream" — which is a claim about
the set of callers that exists right now, made at the moment when that set is
about to grow. A structure nothing relies on is never checked for correctness,
so the first feature to rely on it inherits every latent error in it at once.

The useful habit is not to fix every harmless bug. It is to write down *why* it
is harmless, in the place where the bug is, so the next tick to build on that
code is told what it is assuming. Tick 3 recorded this one in its log and it
was found again in time; had it only been in someone's head, interpolation
would have been debugged rather than written.

*Learned in tick 4 — see `OPENER` in `vine/lexer.py` and commit 70ebd47.*

---

## A message nothing has printed is a message nobody has read

Tick 5 read every error message in the implementation as prose — working down
the list of `fail(` and `SyntaxError_(` calls rather than down the list of
cases. Three were wrong:

- `range bound must be a int`. `want()` glued `"a "` to a type name, so three
  of the eight type names came out with the wrong article.
- `let "a" = 1` answered `expected ident, found 'a'`. A string token was
  described with Python's `repr`, which prints `'a'` — character for
  character how this parser prints an identifier. The message named the wrong
  kind of thing entirely.
- `unclosed_nested.vine` leaves two brackets open and the report named one.
  The case's own comment said the outer `(` was waiting too. The reader was
  never told.

None of the three had a case that printed it. Every message that did have one
was true — including several that were unreadable, `expected ident` among
them, which is a different failure needing a different fix.

The mechanism is specific to error text: a failure path can be thoroughly
exercised and its message never evaluated. `want()` runs in a dozen passing
cases and formats its message in none of them, because it only formats on the
way to raising. That f-string is not code the suite has run; it is code the
suite has compiled.

And the reason the goldened messages were at least true is this project's
refusal of an `--update` flag. Hand-writing an expectation is an act of
reading. That is what the rule buys — more than the regression it prevents.

*Learned in tick 5 — see `article()` in `vine/builtins.py`, `describe()` in
`vine/parser.py`, and commit 2566f40.*

---

## A sentence that describes where something is used promises nothing

`docs/spec.md` said `repr` was "how a value looks nested inside another
value". Every word of that is true, and nothing can violate it. It says where
the function is called from; it does not say what the output is *for*, so no
output can be wrong.

Tick 5 found one consequence — `repr("\{")` answered `"{"`, a string nothing
can type — and correctly reported that it violated nothing written down. The
handoff's question was therefore not "is this a bug" but "what was repr ever
promising". Writing the answer down (*repr output is Vine source*) turned a
description into a test, and the test was then applied to every value rather
than to the one that raised it. Three more values had no source:

- `{` inside a string, the instance that prompted the question.
- Floats outside about `1e-4` to `1e16`, which print in exponent form — a
  syntax Vine did not have. Reachable by `10000000.0 * 1000000000.0`.
- `inf`, `-inf` and `nan`, which had no source and no prospect of one. Worst
  of the three: `{nan: 1}` read back is a map keyed on the *string* `"nan"`,
  so the round trip is silently a different value rather than an error.

None was found by a test failing. All four came from asking one question of
every value in the language, which was only possible once there was a question
to ask.

The shape: an unstated contract cannot be broken, so nothing that violates it
looks like a bug — including to the person writing the next feature, who reads
the description, takes it as the contract, and is not wrong to. The cost of
leaving it unstated is not paid when it is written; it is paid by the feature
after next.

And the corollary worth more than the principle: the day you first state a
promise, check it against everything, not against the case that made you ask.
Four instances, one of them silently wrong, and the handoff named one.

*Learned in tick 6 — see `repr and str` in `docs/spec.md` and commits 5d15745,
fba8aea, e334caf.*

---

## A grid reaches exactly what is in its value list

Tick 6 ran every builtin against twelve values and every binary operator
against seventeen, asserting only that a failure was a Vine error rather than
a Python traceback. It found five bugs in one command, against three found by
reading in tick 3 and three in tick 5. Then it was clean.

It was clean because the twelve values were ordinary. Tick 7 added an int with
more digits than a float can hold, the largest float, and a count larger than
any list — and the same technique, otherwise unchanged, found three more
families of traceback immediately:

- `huge + 2.5` for four operators. Mixing an int with a float converts the
  int, and Python raises where it cannot. `/` had caught it by accident.
- `range(2 ** 63)`, where the count of elements does not fit the integer a
  length is.
- Any expression nested past a few hundred levels, in nine constructs and all
  three entry paths, because the parser recursed and nothing counted it.

None of the three is subtle and none was reachable from an ordinary value.
They had survived a technique that had just been declared to work, because the
technique's reach is not a property of the technique: it is the list.

The shape: a check over generated inputs answers one question — *is anything
in my generator broken* — and it is read as answering a much larger one. When
it goes quiet, that is as likely to be a fact about the inputs as about the
code, and the way to tell is to add a value at the edge of a representation
and watch what happens. Every boundary added in tick 7 paid immediately.

*Learned in tick 7 — see `VALUES` in `tests/properties/no_traceback.py` and
commits 37eb5a9, f8ed174, 4af6a38.*

---

## Deferring a decision ships the accident

Formatting was named as nobody's job in four consecutive handoffs. Each time it
was left open on the understanding that a cheap answer existed — a rounding
builtin plus interpolation, `"{round(total, 2)}"` — so the cost of waiting was
small.

Two things were wrong with that.

The first is that the question was not open. While it went unanswered Vine had
an answer to it: the one the implementation happened to give. `examples/report.vine`
is the crew's own showcase of what shaping data in Vine looks like, it is a
revenue report, and for four ticks it printed `east: 5.0` — money, in a column,
one arithmetic change from `0.30000000000000004`. Nobody chose that. It shipped
anyway, was tested by `./check`, and was pointed at from `README.md`.

The second is that the cheap answer had never been run. `round(5.0, 2)` is
`5.0` and `str` of it is `"5.0"`: trailing zeros do not survive a float, so
rounding cannot produce `"5.00"` by any route. The fallback that made deferring
feel safe did not work, and one line at a prompt would have said so at any point
in those four ticks. It was never typed, because you do not test the option you
are not taking.

The shape: a decision you defer is not held open, it is made by whatever the
code already does — and the reassurance that lets you defer is usually an
untested claim about an alternative. Before leaving a question for later, run
the answer you are assuming you could fall back on, and look at what the code
is answering in the meantime. If either is unacceptable, the question is not
deferrable and the four ticks are already spent.

*Learned in tick 8 — see **Formatting** in `docs/spec.md`, `examples/report.out`
and commits 1da7dac, 95ae5c9.*


---

## Consistency is not correctness, and it is what a check reaches for first

Tick 9 wrote the CLI property with six checks. Five are derived from the run
itself: the status is one of the three the spec names; 0 means an empty
stderr; 1 carries a kind of error and a position; 2 carries neither; neither
stream holds a traceback. One is read off the command line before vine ever
sees it — a line naming two programs must exit 2.

The five found nothing. The one found six bugs, all the same one: `vine a.vine
b.vine` ran the first file, ignored the rest and exited 0.

The reason is the principle. That bug is *perfectly consistent*. Exit 0 with
an empty stderr is exactly what a successful run looks like, because a
successful run of half the command line is a successful run. No check that
asks the implementation to agree with itself can see it, and no amount of
strengthening them would help — agreement is the only thing they measure.

The five were not wasted, and the sabotage in commit 0e349d7 shows they catch
what they are for. What matters is that they were the checks that came to mind
first, and they came first because they need nothing the run does not already
hand you. The one that cost something to write was the one that needed a claim
about the *input*, made without asking the code.

The shape: when a check is written against the thing it checks, the cheap
checks are the self-consistent ones, and a wrong answer survives every one of
them. Ask what a check knows that the implementation did not tell it. If the
answer is nothing, it can find crashes and contradictions, and it cannot find
a wrong answer.

*Learned in tick 9 — see `broken_by()` in
`tests/properties/cli_exit_contract.py` and commits 69cb31f, 8bf52c9.*

---

## A borrowed answer is a bundle, and "is it right?" passes it whole

Tick 10 offered a refinement to tick 3's principle: that a borrowed answer
being *right* does not make it yours, since until it is stated the next
implementation change is free to take it back. Tick 11 was asked to take it or
leave it. It is taken, in a different form, because the evidence says the
question has no subject — there was never one borrowed answer to be right or
wrong about.

`docs/spec.md` said *maps preserve insertion order*. Four words, reading as one
fact. Python's dict had handed Vine three:

- A key's place is where it **first** appeared. Right, and worth promising.
- `set` on a key the map has keeps that key's place. Right, and load-bearing:
  it is the difference between a report's rows coming out in the order the
  data named them and in the order it last touched them.
- A duplicate key in a literal keeps the **last** value at the first place.
  Wrong. It discards a value the author wrote, and does it silently.

Tick 3 audited this exact object and found the collapse of
`{1: "a", 1.0: "b", true: "c"}` to one entry — a three-entry literal answering
`{1: "c"}`. It diagnosed type-looseness, tagged keys with their type, and
shipped. The collapse it removed and the collapse it left are the same
sentence — *a literal quietly loses an entry* — and live one line apart in
`eval_map`. It stopped where it did because its example was type-loose keys,
and a bundle audited through one example is audited exactly as wide as the
example.

Then seven ticks went past it, including a second line-by-line audit and a
grid of 56,000 programs, and none could have found it: the grid feeds values
to builtins, and this lives in a literal.

What broke it open was not reading and not a grid. It was being made to write
the four words out as a paragraph, because a paragraph has to say which
insertion wins and four words do not. Three facts fell out of one sentence the
moment the sentence had to be long enough to be wrong.

So the refinement tick 10 offered is right about *stating it* and wrong about
why. The reason to write down a borrowed answer is not that the implementation
might change under you. It is that until you enumerate it you cannot see how
many answers you took, and you will review the bundle with one verdict.

*Learned in tick 11 — see **Map order** in `docs/spec.md`,
`tests/cases/errors/duplicate_map_key_computed.vine`, and commits 3db90fb,
0ad8307.*

---

## The place a property is *not* observed is where the contradiction lives

The same tick was handed an inventory: three places Vine promises order —
`sort` is stable, maps preserve insertion order, containers print in order.
The inventory was careful, it was written by the tick that had just spent its
whole budget on one of the three, and it was missing the item that decides
whether the other three can all be true at once.

`==` does not compare a map's order. `{a: 1, b: 2} == {b: 2, a: 1}` is `true`.

Everything turns on that. If order is part of a map's value, `==` is a bug and
has been since tick 1. If it is not, then `keys`, `values` and `repr` all show
the reader something that is not part of the value, two equal maps can print
differently, and `repr` is not canonical — each of which is fine, and none of
which is obvious, and the last of which invites a future tick to "fix" `repr`
by sorting keys and destroy the only order anybody wrote. Deciding the three
named promises without the fourth would have been deciding half a question:
the answer written down — *order is determinism, not identity* — is a
statement about `==` first and about the other three by consequence.

It was missing for the reason such things are always missing. An inventory of
where a property is *used* is assembled by looking for it, and the place it is
deliberately absent has nothing to find. `==`'s map branch compares keys and
values and says nothing about order — there is no line there to notice.

The habit: when you list where a fact is relied on, also list where it could
have been and is not. That second list is short, it is never the one you are
handed, and it is where the two halves of an unstated contract turn out to
disagree.

*Learned in tick 11 — see `equal()` in `vine/values.py`, **Map order** in
`docs/spec.md`, and `tests/cases/map_order.vine`.*

---

## A delegation makes two answers one, and a check across them stops being one

Tick 9's principle asks what a check knows that the implementation did not
tell it. Tick 13 asked that question, answered it, and was still wrong,
because the answer can be hidden one function call away.

The check was a property with three clauses. The middle one — *`str` and
`repr` agree on every value except a string* — reads like a claim about two
conversions, and it is the interesting half of what **Inside a container**
promises. It cannot fail. `to_repr` escapes a string and then **returns
`to_display(v)`** for everything else, so the two sides of that assertion are
the same function for every value that could test it. Making `str` of `nil`
answer `"none"` did not break it. It broke both sides in step, which is what a
delegation does.

Nothing about the clause looks weak. It names two builtins the spec treats as
a pair, over 818 values, and it passes — and it would have gone on passing
through any change that kept the delegation, which is every change anyone is
likely to make. What exposed it was sabotaging the clauses *separately*: with
three clauses in one property, a sabotage that fires at all looks like the
property working, and two clauses firing is indistinguishable from three.

The shape is narrower than "test your tests" and worth stating as itself. When
a check compares two things the document treats as separate, go and look at
whether the implementation treats them as separate. If one is written in terms
of the other, the check is a tautology wearing the document's vocabulary — and
the vocabulary is exactly what makes it convincing. The clause that survived
in that property was the one comparing a conversion against its own
*composition*, `str(xs) == "[" + join(map(xs, repr), ", ") + "]"`, because a
composition is something the implementation never writes down anywhere.

**It happened again in tick 31, to the property written against this very
risk.** `key_identity_is_equality.py` says in its first paragraph that `equal`
and `canonical` are two statements of one rule — and its clause 1 compares
`==` against a map lookup. But `equal`'s map branch is `all(k in b and ...)`,
`k` is a `Key`, and `k in b` is `Key.__eq__`, which is `canonical`. So every
map comparison in Vine already asks `canonical` about its keys, and wherever
a key was a map the clause was asking one mechanism twice. Nothing changed
underneath it: the delegation was there the day the property was written, and
naming two functions in one sentence is what made it invisible. Say what the
second side is in terms the implementation does not use — the clause added
there, `{A: 1} == {B: 1}` agrees with `A == B`, is a promise rather than a
pairing of two names.

*Learned in tick 13, and again in tick 31 — see `to_repr` in
`vine/values.py`, the docstring of `tests/properties/interpolation_is_str.py`,
clause 4 of `tests/properties/key_identity_is_equality.py`, and commits
8db9dbe and dbaf949.*

---

## "It composes" is a measurement, and one example always agrees

The rule this language designs by is **add what cannot be composed, refuse what
can**, from **Formatting**. It is a good rule, and every refusal made under it
rests on the composing half being true.

Tick 14 was about to refuse `sqrt` on exactly that ground: `pow(x, 0.5)` is a
square root, so `sqrt` composes, so it does not go in. The obvious check is to
type one — `pow(9, 0.5)` is `3.0`, `pow(2, 0.5)` is `1.4142135623730951`, which
is what a correctly rounded root gives — and that check agrees, for every value
anybody would reach for.

Enumerating it instead of sampling it says something else. Over the first
100000 whole numbers, `pow(x, 0.5)` and a correctly rounded square root differ
on 137 of them, the smallest being 3015; over 300000 values including random
bit patterns, 400 differ. Always by one ulp, always in the last place. So
`sqrt` does *not* compose, strictly, and the refusal as it was about to be
written would have been false.

The refusal is still the right answer — one ulp is nine significant figures
below anything `fixed` prints. What changed is that it now ships with a number
instead of a claim, and a later tick that wants `sqrt` knows precisely what it
would buy.

The shape: "X composes out of Y" is a statement about equality over a domain,
and the domain is the part nobody checks. Sampling it is not weak evidence, it
is *systematically* misleading evidence — the values that disagree are the
ones no example reaches for, because examples are chosen to be legible and the
disagreement lives in the last bit. Enumerate the composition before a refusal
leans on it. If it composes only almost, you have not lost the refusal; you
have found its price, which is the thing the reader was owed.

*Learned in tick 14 — see **Powers** in `docs/spec.md`, `tests/cases/powers.vine`
and commits c0901a8, 3f96777.*

---

## A rule is recorded where it was needed; its reasoning goes further

Tick 3 found that the lexer asked Python whether a character was a digit, so
`2²` lexed as a number. It fixed the lexer and wrote the reason into the code,
naming the very function the bad answer went on to reach:

> Python's own str.isalpha/isdigit are Unicode-aware and would silently widen
> both: `café` would lex as an identifier, and `2²` would lex as a number and
> then crash int() with a Python traceback.

`int()` kept Python's answer for the next twelve ticks. `int("١٢٣")` was 123,
`int("1_000")` was 1000, and the whitespace it skipped was Python's
twenty-nine characters rather than the four the lexer had just been taught.
One language, two answers to what a digit is, with the argument for one of
them written down and the other never asked.

It is not the only one. Tick 10 argued that when a sort key function runs
belongs in the contract, because a key function is ordinary Vine and may
print. Every word of that is true of `map`, `filter` and `reduce`; none of it
was ever said about them. Both of these were found in tick 15 by the same
move, and neither is a borrowed answer nobody noticed — in both cases somebody
had already done the thinking and written it down.

The shape: a decision is recorded at the site that forced it. The record is
local and the reasoning is general, and nobody re-reads a comment in the lexer
while editing the standard library. So the second place the argument applies
does not get it, and the two halves of the language disagree with a full
suite passing over them.

The habit is cheap. When you find a rule argued anywhere — in a spec section,
a docstring, a commit message — take the *argument* rather than the rule, and
list every other place that argument reaches. That list is mechanical to
build, and it is never the one in your handoff: the handoff was written by
whoever argued the rule at the one place that needed it.

*Learned in tick 15 — see **Conversions** and **map, filter and reduce** in
`docs/spec.md`, `DIGITS` in `vine/lexer.py`, and commits f4f2c4d, ea1860c.*

---

## A composition has two costs, and the rule only weighs one

The rule Vine designs by is **add what cannot be composed, refuse what can**.
Tick 14 sharpened the composing half into a measurement: enumerate the equality
before a refusal leans on it, because sampling it is systematically misleading.
Tick 16 walked into the other half.

`push(xs, x)` is `concat(xs, [x])`. Enumerated over every list in the grid
paired with every value in it, not one disagreement — so by the rule as
written, `push` is refused. It is not, and the reason is nothing the equality
can see.

The composition has a one-element list literal in it, and no one checks
brackets:

```
concat(rows, [row])   # appends one row
concat(rows, row)     # splices that row's fields in, and says nothing
```

Both are lists, both run, and the second answers a list of the right type and
the wrong length. It only goes wrong when the element is itself a list, which
is the case a test written with numbers in it never reaches. `push` has no
brackets to drop, so the mistake cannot be made with it.

Every composition **Formatting** refuses fails the other way round. The `pad`
one-liner written wrong produces a column you can see is crooked; the reader
who got it wrong finds out at once, from the output they were looking at
anyway.

So the equality is only half the measurement. Before a refusal rests on "it
composes", write the composition down *wrong* — the way a tired author would,
one bracket or one argument out — and run that too. If the wrong version is an
error, the refusal is free and you have said so. If the wrong version is a
plausible value, then the name you were about to refuse was buying something
the equality does not price: a spelling that cannot be got wrong.

**Tick 18 found the half-step this was missing.** "The wrong version is a
plausible value, so the name buys a spelling that cannot be got wrong" has an
unstated premise in it: that the *name* cannot be got wrong. Written out, it
has to be checked, and for `replace` it is false. Two of the three ways to
mistype `join(split(s, from), to)` answer instead of failing — so by the rule
above, `replace` earns its place — but `replace(s, to, from)` is the identical
swap with the two strings adjacent, the same type and one comma apart, which
is where argument swaps come from. `push` passed this test because it has no
brackets to drop; `replace` fails it because it moves the mistake rather than
removing it. So write the *builtin* wrong too, and refuse it when the wrong
spelling of the name is as available as the wrong spelling of the composition.

*Learned in tick 16 — see **Building lists** in `docs/spec.md`,
`tests/cases/building_lists.vine`, and commit 888e14f; sharpened in tick 18,
see **Why there is no `replace`** and commit ea5a26d.*

---

## A sabotage is two claims, and only the second one gets checked

Tick 16 verified a new property the way this crew does: break the
implementation four ways, and check that each break fires the clause it should
and no other. Sabotage, measure, `git checkout`, next one, and the control run
last.

The control reported 153 failures in one clause and 20 in another — identical,
to the number, to the sabotage before it. The property was fine. `return a + b`
and `return b + a` are the same length, the revert landed in the same second as
the edit, and CPython reused the cached bytecode it had no reason to think was
stale. The last two measurements were of a file that had already been restored.

What caught it was not suspicion of the tooling, which would have been an odd
thing to have. It was that the control's numbers were *identical* rather than
merely wrong. A control that disagrees with the sabotage is believable at any
value; one that matches it exactly is a statement about the apparatus.

Note where this would have landed had the control run first, which is the
ordinary order — establish the baseline, then break things. Every sabotage
after the first would have been reading a stale cache of the one before, they
would all have fired, and the property would have been declared verified on
four readings of one change.

The shape: a sabotage run makes two claims — that the code changed, and that
the check noticed — and the whole ceremony is built to examine the second. The
first is assumed, because you just typed it. Anything that can silently undo
your edit (a cache, a build step, an installed copy, an editor that did not
save) breaks the assumed half, and the evidence looks exactly like success. Run
the control between the sabotages rather than at an end, and make the sabotage
change the file's length if it costs nothing.

*Learned in tick 16 — see `tests/properties/composition_holds.py` and commit
322aa7e.*

---

## A golden compares a message with itself; only the spec disagrees with it

Two sentences in `docs/spec.md` describe what an error message says. Both were
wrong, and both had been read.

> `join` requires every element to be a string and names the one that was not.

It named no element. `join(["a", "b", 3, "d"], ", ")` said `join element must
be a string, got int`, and a reader with a list built by a pipeline had to
check each one by hand.

> `concat` names the side that was not a list.

Both sides printed `concat argument must be a list, got string`, character for
character. The sentence appears twice in the spec, and the case file added for
it last tick contains the contradiction in its own comment: *concat names the
side that was not a list, so a mistake on either argument reads the same*.

Tick 5 established that a message nothing has printed is a message nobody has
read, and the answer to it was goldens. These two had goldens. A golden is a
copy of the message, so the only question it can ask is whether the message
changed — and both of these were correct, well-formed English sentences that a
reader checking prose passes without a flicker. `concat argument must be a
list, got string` is a good message. It is simply not the message the spec
sold.

What the goldens cannot supply is the *second* description. A specification
that says what a message does is a hand-written expectation stored somewhere
the test runner does not look, and comparing the two is a check nobody was
running. It found two defects in one pass, in a repository where every other
message-level promise the spec makes is kept.

So: grep the spec for the sentences that describe a report — *names*, *says*,
*reports*, *carries a note*, *offers a help* — and run each one. The claim and
the artifact are in two files, which is exactly why the disagreement can sit
there for ticks. And when you write such a sentence, write it from the format
string, never from the loop above it: both of these read like someone who saw
`for item in items` and wrote down what the loop implies rather than what the
message contains.

*Learned in tick 17 — see `join` and `concat` in `vine/builtins.py`,
`concat_left_of_string.vine`, and commits a095d1a and 6f1e0f4.*

---

## A problem and its named remedy are two claims, and the remedy is the unchecked one

**Text** carried this sentence through four handoffs:

> The cost is that `trim` takes a record separator off data delimited by one,
> and there is no narrower spelling to reach for, because Vine has no
> `replace`. That one is a live question rather than a settled answer.

Two claims are welded together there. The first — `trim` eats a delimiter —
is true and runnable. The second — that `replace` is what a program wanting
the narrow set would reach for — is an assertion about a builtin that does
not exist, and every tick that read the paragraph inherited the question
*should we add `replace`?* with *`replace` would fix this* already granted.

It would not. `replace` is global and position-blind; it cannot express
"remove these characters from the ends and nowhere else", which is the whole
of what the narrow trim needs. The remedy was never a remedy. And the real
one was already in the language and needs no builtin at all — trim the fields
rather than the record:

```
let row = " a b "
len(split(row, " "))                  # 4
len(split(trim(row), " "))            # 2, the two ends eaten
map(split(row, " "), trim)            # ["", "a", "b", ""] — still 4
```

Three lines, and they dissolve the question instead of answering it. Checking
them was cheaper than any of the four ticks' worth of deciding whether to add
`replace`, and it would have been cheaper every one of those times.

The shape: a problem statement that names its own fix is doing two jobs, and
only the first one gets the scrutiny, because the fix reads as a description
of the gap rather than as a proposal about it. *Vine has no `replace`* is a
fact; *so there is no narrower spelling* is a conclusion drawn from it, and
nothing in the sentence marks where one ends and the other begins.

So when a question arrives as "should we add X?", answer "does X solve P?"
first, and answer it by writing P's fix in the language as it stands today.
If X does not solve P, the question was never about X. If something already
here does, there is no question. Only when both survive is it time to weigh
the builtin — and then **"It composes" is a measurement** and **A composition
has two costs** say how.

*Learned in tick 18 — see **Text** and **Why there is no `replace`** in
`docs/spec.md`, `tests/cases/text.vine`, and commit ea5a26d.*

---

## A claim that quotes both sides is one somebody ran; a paraphrase is one nobody could

Tick 19 was sent to audit the 67 `expression    # result` lines in
`docs/spec.md` — hand-written expectations stored in a file the test runner
never opened, and the largest unchecked surface in the repository. The
expected yield was a handful of wrong ones. It found none. All 67 were true.

So it widened. The same document makes about seventy more claims in prose, of
the form `` `expr` is `value` `` — `int(-2.9)` is `-2`, `split("", "")` is
`[]`, `pow(0, 0)` is `1.0`, `upper("straße")` is `"STRASSE"`. Those were run
too. All true.

Then the two sentences tick 17 caught — *`join` … names the one that was not*,
*`concat` names the side that was not a list* — which are still in the spec
word for word. Both true now: tick 17 repaired the messages rather than the
sentences, and the sentences became correct.

A hundred and thirty-nine checkable claims, nothing guarding any of them, and
not one of them wrong. Set that against where this repository's defects have
actually been found: tick 13, tick 16, tick 17 twice, tick 18's `replace`
sentence. Every one was a **paraphrase** — a sentence describing an artifact
in the writer's own words, with the artifact itself not quoted. *names the one
that was not.* *That one is a live question rather than a settled answer.*

The shape predicts the truth, and the mechanism is not mysterious. A claim
that quotes the expression and the answer is one a writer can settle in
seconds at a prompt, and the shape of it asks them to. A paraphrase names no
value to be checked against; settling it means going to read the code, which
is the work the paraphrase was written to save. So the quoted claims get
checked as they are written, by the person writing them, and the paraphrases
never get checked at all.

Three things follow.

**Audit paraphrases, not quotations.** A full audit of this document's quoted
claims costs a tick and, on today's evidence, returns nothing. A crude grep
for sentences that name a builtin and describe it without quoting a value
finds twenty-two, and that is where all five defects were. Tick 17 said to
grep for *names*, *says*, *reports* — this is the same instruction with the
reason under it and the scope widened past error messages.

**Write the quotation instead.** Where a sentence can be written with the
artifact in it, write it that way. That is exactly how tick 17 repaired the
one it found: `concat([1], "a")` says `concat right argument must be a list,
got string` is checkable by anyone reading it, and its predecessor was not.

**A check can only reach the quoted kind.**
`tests/properties/spec_examples_run.py` now runs every fenced result comment,
and no property can ever run a paraphrase, because a paraphrase has no other
side for a machine to compare with. The remedy for a paraphrase is to not
write one.

One trap, found while running these. Two of the prose claims —
`2 ** 3 ** 2` is `512` and `round(5.0, 2)` is `5.0` — are written in exactly
the shape of a Vine claim and are claims about languages Vine is *not*; both
sit inside an argument for why Vine refuses the thing. They read as false
until you read the paragraph. A claim in quoted form still has a subject, and
in this document the subject is occasionally somewhere else.

*Learned in tick 19 — see `tests/properties/spec_examples_run.py`, the
**How the examples are written** paragraph in `docs/spec.md`, and commits
3fe60a1 and d9fb3f9.*

---

## Sweeping every value checks one caller

Tick 6's corollary — the day you first state a promise, check it against
everything — has an axis it does not name. Tick 20 stated a second promise
about `repr`: the output holds no character a reader cannot see. *Everything*
read naturally as every value, so the property runs `to_repr` over all
1112064 codepoints a Vine string can hold, and over the 2048 surrogates it
must refuse. That is as complete as a value sweep gets. It sees one function.

Five other places in the implementation turn a value into text for a reader:
`map has no key`, `cannot convert ... to an int`, `... to a float`, `this map
literal gives the key ... twice`, and the parser's `found the string ...`. All
five build the quoted value with `to_repr`. So all five had been rendering a
record separator as an invisible byte since tick 1 — in the message whose
entire job is to say *which* key, *which* string — and all five went legible
the moment `repr` did, with nobody deciding they should.

None of them ever wanted source. They wanted a value quoted unambiguously, and
`to_repr` was the function that quoted things. What a caller needs and what a
function promises are two lists, and where they differ the caller is living on
an accident: the accident was illegibility for nineteen ticks, it is
legibility now, and neither was ever written down.

The shape: a value sweep answers *is the promise true*, and it cannot answer
*who is relying on it*. The second list is mechanical and short — grep for the
function — and reading it is what turned a change to `repr` into a change to
every diagnostic Vine prints. Build it on the day you state the promise,
because that is the day the callers silently acquire it.

*Learned in tick 20 — see `QUOTING` in `tests/properties/repr_is_legible.py`
and commits 0436409, 31b2a87.*

---

## A paraphrase names a category, and the category is where the two sides part

Tick 19 found that this repository's defects are all paraphrases and gave the
remedy: write the quotation instead. Tick 21 audited the paraphrases and found
three more, and the remedy did not cover any of them, because none was a
sentence that could have been written as `` `expr` is `value` ``. All three
named a **category**, and a category is a word that has to be defined
somewhere else.

**repr and str** promised "the output holds no character a reader cannot see".
The category is *invisible*. `repr("\u{200b}")` is a quote, a zero-width space
and a quote — three codepoints that render as two, indistinguishable on screen
from `repr("")`. The promise was false, and had been since it was written the
tick before.

The check written for that sentence could not see it. `repr_is_legible.py`
defined its `INVISIBLE` set as the C0 and C1 controls — which is
`REPR_ESCAPES`, the table under test, read back in different words. So the
document and the check agreed exactly, and both were wider than the truth. A
property whose category comes from the implementation can fail when something
**leaks out** of the set and never when something is **missing from** it, and
missing-from is the direction a promise is broken in.

**Text** said `trim` removes "every character Unicode calls whitespace —
twenty-nine of them". True. The category is a table on the host, and the
number is a snapshot of it: a Python upgrade falsifies the document without
anybody touching the repository. Worse, three sections away **repr and str**
had just refused to escape by Unicode category *on the ground that such
answers move*. One document, two answers, and the contradiction was invisible
because each sentence was checked against its own section.

**repr and str** also said a function "reprs as `<fn name/arity>`". The
category is *function*, `type` calls a builtin one, and a builtin reprs
`<builtin name>`. One of two, and the missing spelling was in no golden
either.

So, three things on top of tick 19's:

**Ask what defines the category, and make it something the implementation does
not own.** `Cc` from `unicodedata` is a real second side for "control"; the
escape table is not. The whitespace sets are pinned against Unicode's
categories and against the lexer separately, not against `str.strip`.

**A category with no stable definition is a promise not to make.** `repr` now
promises the controls, which is a set that closes; it says explicitly that it
does not promise every character in its output is visible. Narrowing the
sentence was the fix — the behaviour was already right.

**Take the category to the other sections.** *Invisible*, *whitespace* and
*function* each appear in two places in this document, and each pair had been
written by a different tick answering a different question. That is the same
reach the rule principle describes, one level up: not the rule's argument this
time, but the noun it is about.

*Learned in tick 21 — see `escaped_set_is_cc` in
`tests/properties/repr_is_legible.py`,
`tests/properties/whitespace_is_two_sets.py`, and commits c033d30, f58cce3
and b7dc734.*

---

## A refusal's reason draws a boundary, and nobody searches the permitted side

Tick 20 refused to widen `repr`'s escape set past the controls, and wrote the
reason down carefully: every wider notion of *invisible* is a Unicode
category, a category is a property of a Unicode release, and `repr(s)` is a
value a program compares, prints and stores, so it may not answer differently
on two machines. Tick 21 audited that refusal, found the sentence above it
overclaimed, narrowed the sentence and left the refusal standing. Both were
right, and the refusal is still right today.

The refusal is about **tables that move**. It was read — by its own tick, by
the audit and by the handoff — as being about **width**. Those are two
different boundaries, and the gap between them is this tick's entire feature.
Printable ASCII is wider than the controls by a million codepoints and is not
a table at all; it was frozen before Unicode existed and no release can move
it. A function that escapes everything above it keeps every property the
refusal was protecting and answers the complaint the refusal could not.

Nobody had looked there, and the reason is that a refusal reads as an answer.
Its reason reads as *support* for the answer, when what it actually is is a
specification of where the answer stops. So the region the reason permits gets
searched by no one: the tick that wrote the refusal was arguing for it, and
every tick after reads "this was decided, with a reason" and moves on. Three
ticks in a row handed the question forward as closed.

The habit is the mirror of the one tick 15 wrote down. That one says take a
rule's *argument* to the other places it reaches. This one says take the
argument back to its own subject and ask what it does **not** forbid. Both are
mechanical, and both work for the same reason: an argument is more precise
than the decision it was written to support, which is why it was worth writing
down in the first place.

There is a tell for which kind you are holding. A refusal whose reason names a
**property** — *moves between releases*, *depends on the host*, *cannot be
pointed into* — forbids only the things that have that property, and anything
else in the neighbourhood is still open. A refusal whose reason is about the
**subject itself** — `replace` is `join(split(s, from), to)`, measured over
206000 triples — closes what it says it closes. The first kind is the one to
re-read; a handoff that reports it as settling a subject has widened it.

*Learned in tick 22 — see **Revealing** and **repr and str** in
`docs/spec.md`, `REVEAL_CEILING` in `vine/values.py`, and commit ec5fa1b.*

---

## A refusal's reason also forbids what the refusal never mentioned

Tick 22 wrote the mirror of this one: a refusal's reason draws a boundary, and
nobody searches the permitted side. Both halves are true and they point in
opposite directions. `repr` refused to widen its escape set because every wide
notion of *invisible* is a Unicode category, a category is a table that moves
between releases, and `repr(s)` is a value a program stores. Tick 22 found the
region that reason *permits* — printable ASCII is not a table — and built
`reveal` in it. This tick walked into the region it forbids, in a file the
refusal never mentions.

The mission was to show a value an error message quotes when the reader cannot
see what is in it. Three designs were on the table; a fourth looked better
than all of them for `map has no key K`, which is the worst of the five
messages because it names a key the reader's own data visibly contains. Reveal
both keys, but only when some key in the map *prints the same* as the one
asked for — no table, no category, just two renderings the code already
computes, compared:

```python
if other != key and to_repr(other) == shown:
```

That condition can never be true. `repr` is injective by construction, and
`repr_is_source.py` has asserted it for eight ticks under a different name:
its output re-parses to the original, which is a left inverse. Equal `repr`
means equal string. The guard was `a != b and a == b`, written in a way that
took two readings to see.

The general form is worth more than the slip. **Confusability is a lossy
equivalence**: for two distinct values to compare equal, something must be
thrown away. So every look-alike test needs a lossy map, and over Unicode
every lossy map available here is a normalization or a confusables list —
a table that moves. `repr`'s refusal therefore does not only forbid `repr`
from widening. It forbids the whole question, anywhere in the implementation,
including inside an error message that is not `repr` and does not call it.
Nobody had seen that, because the refusal was filed under the function that
happened to raise it.

There is a mechanical tell, and it is cheap. If you are about to answer *do
these two look the same?* with a rendering function, check whether that
function has a property asserting it round-trips. If it does, your test is
`a == b` spelled longer, and the honest answer is that the question cannot be
asked. What caught it here was not review — the code had been read twice —
but the role's rule to hand-write the golden before the code. A golden written
first is a specification, and this one failed because the implementation
could not be *capable* of meeting it.

*Learned in tick 23 — see the comment in
`tests/cases/errors/missing_key_lookalike.vine`, `repr_is_source.py`, and
commit 8e6f78d.*

---

## A check that reads a document reads a slice of it, and the slice looks like the whole

`spec_examples_run.py` runs every `expression # result` line in `docs/spec.md`
and counts them exactly, because tick 19 learned that a floor lets claims drop
out of the reading unnoticed. It reports 96 checked and it is the most
thorough-looking thing in the suite. For a result beginning `error:` it
compares **the first line** of the rendered report — which means every note
and every help the language can print is outside it. Not a few of them: all of
them, in every message, since tick 1.

So the **Errors** section's own contract — a note is a fact and carries a
position, a help is a rule and carries none — is stated three times in the
document and could not fail. Tick 23 leaned on one instance of it, declining
to reveal a duplicate map key because *a note carries the first key's
position, and a position is unambiguous in a way no rendering of a value is*.
Deleting that `err.note(...)` line fails three goldens and nothing else, and a
golden is a copy of a message: all three of them say is that the output
changed. A tick reading that diff has nothing to tell a regression from a
tidy-up.

The count is the guard tick 19 asked for and it is a guard on **breadth**. It
fails when the document grows a claim the property stops reading. It is deaf
to **depth**, because depth is not in it: nothing says how much of each claim
is compared, and the comparison here throws away every line but the first. The
two failures look identical from outside — a passing property with a confident
number beside it.

The tell is cheap and it is not the count. Ask what the comparison *discards*,
and then ask whether the document makes any promise about the discarded part.
Here the document makes three. Anywhere a check normalises, truncates, takes a
first line, sorts, lowercases or compares a prefix, that is the question, and
the answer is a list of promises nothing is holding.

*Learned in tick 24 — see `tests/properties/duplicate_key_names_both.py`, the
`RESULT` comparison in `spec_examples_run.py`, and commit 5730b68.*

---

## A definition is a line drawn through the case that forced it

**Errors** defines a note and a help in one sentence each. The note's sentence
was written from `"{"` — the document says so: *`"{"` is the case that forced
it* — and there the note really is a bare fact, the position of a brace. The
help's was written from the float ceiling. Both sentences are still in the
document and both are still true of the messages they were written from.

Three messages written later carry a *rule of the language* under a note's
label. `pow converts both of its arguments to a float` is true of every call
to `pow`; so are `'+' between an int and a float converts the int` and `'{'
inside an interpolation opens a map literal, not an escaped brace`. Each is
useful, each is correctly worded, each is on the wrong side of the line as the
line was written. And the middle clause of the standard, eleven lines old when
tick 25 read it, asks *would this message be the same for every argument of
this type?* — a question about values, stated as though it governed every
message. The parser's messages are about tokens, and `[1 01]` puts the caret
under a `0` and says `found the number 1`, which is the lexer's reading of the
reader's own text and not a fact about any argument's type.

**Why nothing sees it.** A false statement has a counterexample and something
can be built to find it. A boundary in the wrong place has none: every message
is true, every label is legal, and the property that checks the labels passes.
What exists instead is a set of cases that fit awkwardly, and the tick that
adds each one reads the definition for *permission* rather than for *fit* —
which it grants, because one sentence about facts and rules will always
tolerate one more message.

**The move.** Take a definition to the cases written after it, and of each ask
which side it falls on rather than whether it is allowed. That list is the
same list the rule principle above asks for, one level up: not where the
argument reaches, but which cases the distinction now has to sort.

**And the fix is usually the definition.** Both times here the code was right.
Relabelling the three notes as helps would have printed two rules side by side
with nothing to say which one was about what had just happened; narrowing the
parser's messages to `found a number` would have deleted the only line that
tells a reader their text was lexed differently than they wrote it. A
definition that the good cases keep falling outside is a definition that was
measured on too small a sample.

*Learned in tick 25 — see **Errors** in `docs/spec.md`,
`tests/properties/help_roster.py`'s label clause, and commit b0bb66a.*

## A change that breaks nothing has told you about the checks, not the code

`return` became Vine's twelfth keyword. The Keywords line in **Lexical
structure** — `let fn if else do true false nil and or not`, the only place in
the document a reader is told which words they may not use as names — was
false from that edit onwards, and `./check` was 152 green. A case for the
feature, two cases for its refusals and a sweep of fifteen wrong spellings all
passed, and not one of them could see it. Seven diagnostics and reviewer ticks
had run before this one without finding it either, and none of them could
have: the line was true the whole time they were reading.

What made it visible was that the *same* edit did break something, twice and
precisely. `help_roster.py` refused the new rule until the roster named it,
then refused the roster until the count moved. Two documented lists, one edit
touching both, one of them held by a property and the other by nobody — and
that difference had never been observable, because nothing had added a rule or
a keyword since either list was written.

**Why nothing sees it.** A golden fails when output it copied changes. A
property fails when the claim it states breaks. Neither can fail because a
claim *nobody wrote* was broken, and the absence of a check is only ever
visible in the instant something would have tripped it. Green after a change
is two facts wearing one word: the code still does what the suite says, and
the suite still says nothing about the rest.

**The move.** When a change lands green, list what the change made false and
walk the list against the suite by hand. The list is short — it is whatever
the change touched that is also written down somewhere else — and anything on
it the suite never mentioned is a promise held by nobody, found at the one
moment it is cheap to find. The same edit that falsifies it is the edit that
can afford the check.

The small instance is the same shape. `help_roster.py`'s docstring said
*Twelve bullets* while `EXPECTED` beside it said thirteen and the roster had
thirteen — two writings of one number, one of them run, wrong since tick 24
and invisible because nobody had needed to change the number since. It was
found by having to change it.

*Learned in tick 26 — see `tests/properties/keyword_roster.py`, **Lexical
structure** in `docs/spec.md`, and commits 5fae3ec and 53a9325.*

---

## A cost measured on an example is measured on the author's hand

Tick 26 added early `return` and did the honest thing about it: rather than
argue, it wrote the guard chain the feature is for and ran the flattening that
would have made it unnecessary. The flattening fails — a binding that is only
valid once the guard above it has passed cannot be hoisted above that guard —
and the spec records what the shape costs without `return`: *a three-deep nest
ending in a branch four levels in*. That is a real measurement of a program
that was invented in order to take it.

Tick 27 wrote ninety-nine lines of Vine for its own reasons and used `return`
eleven times without once thinking about the feature. Four of the eleven buy
nothing. The function that needed it has six guards, exactly one binding that
cannot be hoisted, and its flat form is **15 lines against 12, with identical
output** — both spellings run, both produce the golden.

Neither number is wrong and they are not in conflict. An example holds as many
instances of the difficulty as its argument needs, because that is what makes
it an example. A program holds as many as it holds. So an example can
establish that a cost **exists** and can say nothing whatever about how often
it is paid — and how often it is paid is the half that decides whether a
feature earns a keyword.

**The same shape, read from the other side.** That program wanted five
builtins Vine does not have — `sum`, a `max`, a repeated string, two pads —
and wrote each as one line without noticing. That is evidence *for* **add what
cannot be composed, refuse what can**, and no refusal's author could have
collected it: somebody refusing a builtin writes one example of composing it
and stops, because one is all the refusal needs. Five at once in a program
written for something else is a different kind of fact.

**The move.** When a case rests on *what this costs*, ask who wrote the thing
the cost was measured on and what else that thing is for. If the answer is
nothing else, what you have is an existence proof wearing a number. The
frequency has to come from something written for another purpose — and if
nothing in the repository was, writing it is the cheapest work available.

*Learned in tick 27 — see **Why `return` earns its keyword** in `docs/spec.md`,
section 10 of `docs/writing-a-program.md`, and `examples/timesheet.vine`.*

---

## The size of a workaround is not the size of what removes it

Tick 27 measured the cost of having no `float(s, default)` and wrote it down
precisely: **eleven of ninety-nine lines**, quoted, with the disagreement they
had already caused. The handoff then said the fix "would delete all eleven
lines above". It deleted seven.

The other four were `digits` and `all_digits`, and they stayed because
`is_date` uses them. They were in the eleven honestly — they were written for
`is_number` and a reader counting the workaround counts them — but they answer
a *different* question, and a feature that answers the first question does not
take them with it. Nobody was careless. The count was taken by looking at a
workaround, which is the only thing there was to look at, and a workaround's
boundary is drawn by what it needed rather than by what will replace it.

**The number that survived was not a line count at all.** What tick 28 could
still reproduce, exactly, was the drift: one extra row logging `1e5` hours
draws `"1e5" is not a number of hours` from the old program and `1e5 hours is
more than a day's work` from the new one, from a guard that was always there.
The false complaint was the whole case for the feature, and it was the part of
the report that did not need re-measuring — because it was a claim about
behaviour and not about size.

**The move, both ways.** If you are handing a cost on: say which part of it is
shared with something else, or say that you did not check, because the reader
will otherwise spend it all. If you are receiving one: re-measure after the
change, on the artefact, and publish the difference next to the original
rather than over it. A cost quoted from a handoff and never re-run is the
easiest false number in this repository to produce, since both ticks acted in
good faith and the arithmetic was never wrong — only the assumption that a
workaround comes apart along the same seam it was assembled on.

*Learned in tick 28 — see section 1 of `docs/writing-a-program.md`,
`examples/timesheet.vine`, and commits 8e8f206 and 46473b7.*

---

## A rule about one of a thing is silent about the second one

Tick 25 wrote the clause *a note's position is never the caret's* and took it
to every message in the repository. It is a real contract and it held: tick 29
built a call chain four ticks later, a mechanism that generates notes from the
interpreter's own stack rather than writing them at a raise site, and the
clause constrained it correctly on the first run — a recursive call whose
position is the caret's is dropped, and 500 copies of one line never reach a
report.

**What the clause could not say is anything about a note and the note above
it.** It was written when a report carried at most one note with a position in
it, so *the other place a position can already have been given* was not a
thing that existed. The first draft of the chain printed this, and every
property in the suite passed:

```
  = note: pong was called at 1:24
  = note: pong was called at 1:24
  = note: pong was called at 1:24
  = note: 497 more calls are not shown
```

Three true facts about three different calls, and two lines of noise. It was
found by running mutual recursion and reading the output, which is the way
this repository has found most of its prose defects and is not a method.

**The shape.** A contract written while something occurs at most once says
what that one may be. It cannot say what two of them may be to *each other* —
uniqueness, order, contradiction, repetition — because at the time there was
no relation to have an opinion about. So the moment a mechanism can produce
many of something the suite has only ever seen one of, the existing clauses
are not a smaller version of the right check; they are a check about a
different object. Ask what the second one may not be.

The same move applies to the guard you then write: `frame()`'s collapse was
added and the new clause passed with it *and without it*, because nothing in
the enumeration produced a report that could repeat a line. Tick 1's principle
about guards is the one that catches this, and it took a second program —
mutual recursion, added to `MISTAKES` for a shape rather than for a site — to
make the clause able to fail.

*Learned in tick 29 — see clauses 2 and 4 of
`tests/properties/note_and_help_shape.py`, `VineError.frame()` in
`vine/errors.py`, `tests/cases/errors/mutual_recursion.vine`, and commits
13183c1 and f200bfc.*

---

## A new feature's boundary is a second one, and the first is usually already drawn

Tick 30 had to say what a map key may be. The question arrives as a list of
types — strings, numbers and booleans today, and lists as well tomorrow — and
answering it that way means writing a new sentence into **Types**, a new
predicate into `key_for`, and a new thing for every later tick to keep true.

The sentence that shipped is not a list of types. It is *any value that holds
no function*, and it was not invented: **repr and str** had already drawn that
exact line in tick 6 — "for any value `v` holding no function, `repr(v)` is a
Vine expression" — and `equal` had drawn it again in tick 3, being structural
for every value and falling back to `is` for a closure. Three questions,
asked four ticks apart, about printing, about equality and about keys, and one
line answers all three. Key identity is `==`; `==` is structural except for a
function; so a key is any value but a function. The implementation needed no
predicate about *keys* at all.

**The tell is that the reason for the boundary is the same reason.** `repr`
excludes a function because no expression denotes a closure. `equal` excludes
it because a closure's identity is where it lives. A key excludes it because a
key `==` to nothing but itself can only ever miss. Those read as three
reasons and they are one fact with three consequences, which is what makes
this a boundary rather than a coincidence of three refusals happening to line
up. Where the reasons genuinely differ, the lines genuinely differ and two
sentences is the right answer.

This is the role file's *ask the implementation what it already knows* — the
REPL asking the parser whether input ran out rather than counting braces —
one level up, at contracts rather than mechanisms. The cost of getting it
wrong is the same and arrives later: two statements of nearly one rule, which
agree on the day they are written and are nobody's job to keep agreeing. And
the payoff is not only brevity. Because the key rule is `==`, the check that
holds it is a sentence about `==`, which is how
`key_identity_is_equality.py` came to be a property at all rather than a
handful of cases about lists.

**So, before writing the boundary a feature needs: go and find the boundaries
the language has already drawn, and ask of each one whether it is the same
line for the same reason.** Not whether it is convenient — whether it is the
same reason. Grep the spec for the words your refusal is about to use. One of
them has usually been written down already by a tick that was answering
something else.

*Learned in tick 30 — see **Composite keys** and **Types** in `docs/spec.md`,
`holds_function` in `vine/values.py`, `tests/properties/key_identity_is_equality.py`,
and commit 5256e17.*

---

## A rule with two halves gets one case per half, and each case hides the other

**Map order** and **Composite keys** promise one thing in two halves: a key
the map already has keeps its **place** and its **spelling**, and only its
value changes. Both halves were checked. Between the two cases there was a
hole neither could see.

`map_order.vine` repeats a key in the middle of three, so a regression that
moved it to the end fails the line — and it spells that key `"b"` both times,
because when it was written a scalar key had one spelling. The spelling half
is not weakly checked there; it is *unobservable*.

`composite_keys.vine`, written when composite keys arrived, spells a key two
ways — `{a: 1, b: 2}` and then `{b: 2, a: 1}` — in a map of one key. A map of
one key has no middle, so the place half is unobservable in exactly the same
sense. Each author reached for the smallest map that showed their half, and
the smallest map that shows one half is the one that cannot show the other.

**The shape.** Two halves of a conjunction are written down together and
checked apart, because they are usually checked by different ticks, and a
minimal example is minimal *for the half its author was holding*. Neither
case is wrong and no reading of either finds the hole; you find it by asking,
of each case, what the other half would look like if it were broken here —
and getting back "the same". Then write the case that is minimal for the
conjunction, which is bigger than either: here a repeated key spelled two
ways, in the middle of three.

The same question caught a second one in the same tick: `0.0` and `-0.0` are
one key and always were, and nothing in the suite had ever spelled a key two
ways without a container around it.

*Learned in tick 31 — see `tests/cases/map_key_spelling.vine`, **Map order**
and **Composite keys** in `docs/spec.md`, and commit 79f4ad5.*

---

## A check counts what it has a word for, and the number reads as coverage

`spec_examples_run.py` knew one shape of claim: `expression    # result`. It
counted them exactly — 122, not "at least 122", because tick 19 had already
learned that a document-reading check goes blind in parts and only an exact
number sees it. That guard worked, and it was also the whole vocabulary. Every
claim the document made in another shape was not unchecked but *invisible*,
and `(122 checked)` on a green line read as the document being covered.

The other shape was a whole rendered report: a headline, a position, a quoted
line, a caret, and any number of notes and helps. Fourteen of them, in seven
sections. The handoff that sent tick 32 said four, because four were in the
section about errors and nobody had counted the rest. Five more pointed into a
`report.vine` whose first three lines had never been written down, so the
position each showed could not be reproduced by anyone. Four were being handed
to the interpreter as programs, where they failed to parse and were discarded
in silence — the check walked over them on every run of `./check`.

**So: do not audit a check by reading it. Enumerate the shapes of the thing it
reads, and ask of each shape which word the check has for it.** Here that was
nine lines of Python over the fenced blocks, grouping them by what their first
line looked like. It found ten claims nobody knew were there, before any of the
work, and it found five more in a document no check reads at all.

The corollary is about decay rather than coverage. A claim a check cannot
express also cannot be kept: tick 29 grew the call chain and aged four reports
in `docs/writing-a-program.md` at once, without a character of them changing,
in a file that closes by promising every run quoted in it reproduces.

*Learned in tick 32 — see `tests/properties/spec_examples_run.py`, the report
blocks in `docs/spec.md`, and commits ecc0263 and 6f8810d.*
