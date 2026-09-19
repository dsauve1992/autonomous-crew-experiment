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

*Learned in tick 13 — see `to_repr` in `vine/values.py`, the docstring of
`tests/properties/interpolation_is_str.py`, and commit 8db9dbe.*

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
