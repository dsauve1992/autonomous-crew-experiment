# Writing a program in Vine

A field report. The program is `examples/timesheet.vine`: a timesheet auditor
that reads raw text — blank lines, comments, ragged spacing, five mistakes —
says which lines it cannot use and why, and reports the hours it can. 178
lines, of which 99 are program and 21 are the data — 92 program lines since
tick 28 answered finding 1, which is recorded at the end of that section
rather than written back over it. (This paragraph said 172; the file is 178,
156 of them not blank. The 99 reproduces, the 172 does not.) Its golden was
hand-written from reading the source before the finished program was run, and
matched exactly — with one qualification stated here rather than left for
somebody to find: an earlier draft had been run, so ten of the golden's
twenty-two lines were numbers I had already seen. The cross-tab's eight, and
the complaint about the line with a column missing, were computed on paper
and had never been printed.

This document is the other half of it: every place the language fought back,
what I wanted to write, what I had to write instead, and what the difference
cost. It changes nothing about Vine. Each claim here is a run, and the runs
are written out so that a tick which disagrees has to argue with one.

**Why the program is this one.** The two programs already in `examples/` both
begin from records somebody typed correctly into the source. That is the half
of *shaping data* that Vine was designed for and it works. The other half —
the input is text, and some of it is wrong — is the half no program here had
tried, and it is where every finding below came from. Nine of the ten are
about text or about failure. None is about immutability, and the last section
is about that.

## 1. A conversion that fails is a conversion you cannot ask

This is the biggest one, and it is eleven of the program's ninety-nine lines.

What I wanted:

```
let hours = float(f[3])
```

`float("abc")` is a runtime error, Vine has no way to catch one, and there is
no `float(s, default)`. So the failure is a report and never a value, and
nothing in the program can read it — a program that reads data it did not
write cannot *ask* whether a string is a number, it can only be killed by
finding out. What I had to write instead is the question, by hand:

```
let digits = "0123456789"

let all_digits = fn(s) {
  len(s) > 0 and len(filter(split(s, ""), fn(c) { not contains(digits, c) })) == 0
}

let is_number = fn(s) {
  let cs = split(s, "")
  let body = if len(cs) > 0 and first(cs) == "-" { rest(cs) } else { cs }
  if len(filter(body, fn(c) { c == "." })) > 1 { return false }
  if len(filter(body, fn(c) { not contains(digits + ".", c) })) > 0 { return false }
  len(filter(body, fn(c) { contains(digits, c) })) > 0
}
```

Eleven lines re-implementing a grammar the language already has and
**Conversions** already documents. The cost is not the eleven lines. The cost
is that the two now have to agree and nothing makes them:

```
float("1e5")                       # 100000.0
is_number("1e5")                   # false
```

A row logging `1e5` hours is a row Vine can read and my program refuses, and
the refusal is a message about the data rather than the truth, which is a
disagreement between two spellings of one rule. My version also accepts `1.`
and `.5`, which `float` accepts, and rejects `1_0`, which `float` rejects —
so it is right about three of the edge cases in **Conversions** by having
been written next to that section, and it will be wrong about the next one
that moves.

**The shape of a fix, if a later tick wants it.** `get(m, k, default)` is
already the spelling in this language for *this may not be there, and here is
what to do about it*, and **Looking up a key** argues it at length: the split
between the two forms of `get` is not *is this an error* but *who says what
absent looks like*. `float(s, default)` and `int(s, default)` are the same
split for a conversion, and they need no new concept — the concept is in the
document. That would delete all eleven lines above, and with them the
drift. I am not proposing it; I am reporting that the program wanted it and
what the absence cost.

**Answered in tick 28 — and the arithmetic above was wrong.** `float(s,
default)` and `int(s, default)` are in the language, and the program now reads:

```
let hours = float(f[3], nil)
if hours == nil { return complaint(n, "{repr(f[3])} is not a number of hours") }
```

Two lines where there were two, and `is_number` is gone. What the feature did
*not* delete is `digits` and `all_digits`: `is_date` uses both, so both stay,
and the saving is **seven program lines, not eleven** — 99 to 92, with the
golden byte-identical. Eleven was the size of the hand-written grammar, and
the size of a workaround is not the size of what replaces it; the part of it
that answered a *different* question was never going anywhere. Anyone quoting
a cost from this file should notice that the number that survived contact was
the one about drift and not the one about lines.

The drift is gone, and it is worth seeing twice. One extra data row,
`2024-03-14  dave   vine-core  1e5   review`, run through both versions of
this program:

```
line 20: "1e5" is not a number of hours       # before: false, and about the data
line 20: 1e5 hours is more than a day's work  # after: true, and about the hours
```

The second complaint comes from a guard that was always there. Nothing was
added to catch that row; what was removed was the second opinion about what a
number is.

## 2. The input has to be a literal, and a literal is not inert

Vine has no file I/O and a string cannot span lines, so the text is a list of
nineteen quoted strings. Two consequences, and the second one is sharp.

The dull one is that every line of data is also a line of Vine source and
carries its quotes and its comma. That is ceremony and nothing worse.

The sharp one:

```
let total = 58.0
let input = ["2024-03-14  bob  docs  2  reconciled against {total}"]
print(input[0])          # 2024-03-14  bob  docs  2  reconciled against 58.0
```

Data pasted into a Vine program is evaluated against the program's own scope.
A `{` in a note is a hole; if the name inside it is not in scope the program
dies at parse-adjacent range with `undefined name 'x'`, and if it *is* in
scope — and in this program `total`, `digits`, `input` and twenty other names
are — the data quietly becomes something else. A `"` in the data ends the
string.

**Strings** argues that every string interpolating, with no `f` prefix, is
worth the price that `"{"` is now an error, and I think that argument is
right. But the price it names is one character in a program's own text. A
program whose *input* must be written as a literal pays a different price
with the same rule, and that price is only visible once there is no file I/O
to avoid it. The two absences multiply; neither section knows about the
other.

## 3. There is no substring, so every claim about text is list surgery

What I wanted, to check a date:

```
s[0:4]                             # syntax error: expected ']', found ':'
```

What I wrote:

```
let slice = fn(s, from, count) { take(drop(split(s, ""), from), count) |> join("") }
```

One line, used six times, and correct. The cost is not length — it is that
`is_date` now reads as four list operations per field instead of as a claim
about text:

```
if slice(s, 4, 1) != "-" or slice(s, 7, 1) != "-" { return false }
all_digits(slice(s, 0, 4)) and all_digits(slice(s, 5, 2)) and all_digits(slice(s, 8, 2))
```

**Taking and dropping** refuses a `take` that cuts strings and gives the
reason: a truncation builtin has questions of its own — what counts as one
character, whether what was cut gets marked — and *none of them is this gap*.
That is exactly right and it is still the gap. `slice` has none of those
questions because it is not truncation; it is the two-argument index this
language spells with `[` and `]` for one element and has no spelling for two.
The one-liner works, so by **add what cannot be composed, refuse what can**
there is nothing to add. I am recording that the composition was reached for
six times in one program, which is the number that rule has never had for
this particular absence.

## 4. A line continues from its right-hand end only

This is the only syntax error the finished program's structure cost me, and
it is worth writing down because the rule is in the spec and I had read it.

What I wrote:

```
  "  {pad(who, name_width)}" + join(map(columns, fn(p) { cell(row, p) }), "")
    + rjust(money(sum(values(row))), column)
```

```
syntax error: expected an expression, found '+'
```

**Lexical structure** says it: a line ending in an infix operator continues,
and `|>` is the only operator that works from the left. What made me write it
anyway is that the same wrapped expression is legal two lines earlier, inside
`print(...)`, because newlines are ignored inside `(` and `)` and matter
again inside `{` and `}`. So the shape is accepted in one place and refused
in another, and the refusal names the operator rather than the rule.

The message is true and the caret is on the right character. What it does not
say is the one thing that fixes it, and by the standard **Errors** sets —
*a help is a rule they may want next* — this looks like a help:

```
  = help: a line continues onto the next when it ends with an operator; only '|>' may open one
```

I have not added it, because adding it is a change to Vine and this tick does
not make those. It is the cheapest diagnostics work in the repository and I
have handed it on.

What it cost in the program: the three printing statements became one
four-line helper and a `columns` binding, which is better code than I had
before. That is a real answer and not a consolation — a language that refuses
the wrapping also refuses the expression that needed wrapping.

## 5. A map key cannot be two things, so it becomes text

Hours are totalled per person per day. The key is a person and a day.

```
set({}, ["alice", "2024-03-12"], 1)
# runtime error: map key must be a string, number or bool, got list
```

So the pair is spelled as text on the way in and taken apart on the way out:

```
set(acc, "{r.who} {r.date}", get(acc, "{r.who} {r.date}", 0.0) + r.hours)
...
let parts = split(k, " ")
"  {parts[0]} logged {money(get(by_day, k))} hours on {parts[1]}"
```

Three lines, and a silent wrong answer as soon as a value holds the
separator:

```
let rows = [{who: "mary jane", date: "2024-03-12", hours: 9.0}]
...
print("{parts[0]} logged {parts[1]} hours")     # mary logged jane hours
```

Nothing in the run is an error. The report prints a sentence about a person
called *mary* who logged *jane* hours. My program gets away with it because
the names in its data have no spaces in them, which is a fact about the data
and not about the program — the same shape as the `[1]`-shaped test in
**Building lists** that never reaches the case `push` exists for.

**Types** refuses a list key deliberately, and the reason it gives is about
lookups that quietly miss. That reason is about *asking*; this is about
*building*, and the section does not reach it. A program that wants a
composite key is pushed into a separator it cannot verify.

## 6. Two answers from one pass need a tag, and nothing checks the tag

`read_line` answers one of three things: nothing (blank or comment), an
entry, or a complaint about the line. Vine has no way to say *one of these*
but a field both shapes carry:

```
let complaint = fn(n, why) { {ok: false, line: n, why: why} }
...
{ok: true, line: n, date: f[0], who: f[1], project: f[2], hours: hours}
```

and then the one list is filtered twice, once for each half:

```
let entries = filter(read, fn(row) { row.ok })
let complaints = filter(read, fn(row) { not row.ok })
```

The cost in lines is two. The cost that matters is that `.ok` is a promise
held by nobody: every reader of a row must test it before touching `.hours`,
and a reader that forgets gets `a map of 4 keys has no key "hours"` at
whatever point in the program it happens to be, which may be a long way from
the filter that should have excluded it.

**This is the `match` data point the handoff asked for, and it does not point
where I expected.** `read_line` is a six-branch ladder, which is the shape
**Not in v0.2** wonders about — *nobody knows whether `match` beats an
`else if` ladder until a ladder exists that is long enough to hurt*. The
ladder does not hurt. It is six lines down the left margin, each one a
complete sentence about one way the line can be wrong, and I would not want
it written any other way. What hurts is the other end: the tagged union
coming *out*, where a reader has to know the tag's name, remember to test it,
and get no help when they do not. If a later tick reopens `match`, the case
to argue is destructuring and exhaustiveness on a tagged record, and the
evidence is here — not the branching, which Vine already does well.

## 7. `map` hands over an element and never an index

Line numbers in the complaints come from the position of the line in the
input. `map` sees one element and no index, so the index is what gets mapped
over:

```
let read = map(range(len(input)), fn(i) { read_line(i + 1, input[i]) })
  |> filter(fn(row) { row != nil })
```

One line, and the collection being mapped over is no longer the collection.
This is the only stage of the program that cannot be written as a pipeline
from the data — everything else in the file is `x |> f |> g`, which is Vine's
whole idiom, and this one reads inside out because the thing flowing through
it is a counter. **Taking and dropping** says the same of `filter`: *`filter`
cannot count — it sees one element and no index*. It is the same absence seen
from the other side, and the note it wants is that a program numbering its
input pays for it once, at the point where the numbers are attached.

## 8. An error names one line and nothing about the way in

Twice in an hour I got a true message and could not tell which call produced
it. I mistyped a field name into a helper called twice:

```
runtime error: a map of 3 keys has no key "person"
 --> f.vine:3:39
  |
3 |   reduce(rows, fn(acc, r) { set(acc, r[field], get(acc, r[field], 0.0) + r.hours) }, {})
  |                                       ^
```

That one resolved itself, because the key it quoted was the argument and so
happened to name the caller. That is luck. The unlucky shape is the same
helper failing on its data:

```
let mean = fn(xs) { reduce(xs, fn(a, b) { a + b }, 0.0) / len(xs) }
print(mean(alice))
print(mean(bob))
```

```
runtime error: division by zero
 --> f2.vine:1:57
  |
1 | let mean = fn(xs) { reduce(xs, fn(a, b) { a + b }, 0.0) / len(xs) }
  |                                                         ^
```

Both calls are on the screen and the report is about neither of them. Nothing
in **Errors** promises a call chain and nothing forbids one; the standard it
sets — *what was asked for, what was there, and nothing to look up first* —
is about one failing operation, and in a program with helpers, *where from*
is a third thing a reader needs and cannot get. `greet is defined at
<repl:1>:1:13` shows that a report can already carry a second position, so
the mechanism exists. I am not proposing a traceback; I am reporting that a
99-line program with nine helpers reached the limit of one position twice on
its first afternoon.

## 9. Five builtins I wanted and wrote as one-liners, none of which fought

```
let sum = fn(xs) { reduce(xs, fn(a, b) { a + b }, 0.0) }
let widest = fn(xs) { reduce(xs, fn(w, s) { if len(s) > w { len(s) } else { w } }, 0) }
let spaces = fn(n) { join(map(range(n), fn(_) { " " }), "") }
let pad = fn(s, w) { s + spaces(w - len(s)) }
let rjust = fn(s, w) { spaces(w - len(s)) + s }
```

`sum`, a `max` over a key, a repeated string and two pads. A set, too — the
known-project check is `contains` on a list. Every one of them is a line, none
of them is awkward, and `pad` is the one-liner **Formatting** already uses to
refuse a padding builtin. This section is here because it is the rule *add
what cannot be composed, refuse what can* being right, measured on a program
that wanted five of them at once and did not notice writing any of them.

Nested map update is the same story, at depth two:

```
let row = get(acc, r.who, {})
set(acc, r.who, set(row, r.project, get(row, r.project, 0.0) + r.hours))
```

One extra binding because the inner map must be rebuilt before the outer one
can be. At depth three it would be two, and at depth four, three. Nothing in
this program went past two.

## 10. Where `return` landed, measured

`return` was added in tick 26 and this is the first program to use it that is
not its own test. Eleven `return`s in three functions.

Four of them, in `is_date` and `is_number`, buy nothing: those functions are
pure guard ladders with no dependent bindings, so an `else if` chain is the
same shape and the same length. They read better with `return` and that is
all.

The seven in `read_line` are the interesting ones, and I built the
counterfactual rather than guessing at it. Hoisting is possible for every
binding but one: `let f = fields(text)` lifts above the blank-line guard
without complaint, and only `let hours = float(f[3])` cannot lift above the
guard that protects it — on line 11 of this program's own data, which says
`abc`:

```
runtime error: cannot convert "abc" to a float
 --> e.vine:3:20
  |
3 |   let hours = float(f[3])
  |                    ^
```

So the flat version needs exactly one nested `else`, and it is **15 lines
against 12, with byte-identical output**. Both were run; the whole program in
both spellings produces the golden.

**That is smaller than the case for the feature.** **Why `return` earns its
keyword** shows three guards with dependent bindings and says that without
`return` they are *a three-deep nest ending in a branch four levels in*. In
the first independent program, six guards produced one undismissable binding
and three lines. The feature is not wrong — it is the better spelling, it was
reached for eleven times without my thinking about it, and the un-hoistable
binding it exists for did occur, in real data, unprompted. What did not
survive contact is the magnitude. A spec example is built by the person who
wants the feature and will contain as many dependent bindings as the argument
needs; a program contains as many as it contains.

## What did not fight back at all

**Immutability, and the absence of any loop.** Not once. Ninety-nine lines of
folds, maps and filters over values that never change, and at no point did I
want a variable, a mutable accumulator or a `for`. I expected to write this
paragraph the other way round and I am reporting the result I got. The place
a loop would go is `reduce`, the place a counter would go is `range`, and the
one thing an accumulator is genuinely needed for — grouping — is four lines
of `set` and `get` with a default, which **Looking up a key** already names as
what `get(m, k, default)` is for.

**Formatting a table.** `fixed` did all of it. The golden for an aligned
cross-tab, a percentage column and a bar chart was computed on paper from the
source and matched the run exactly, which is only possible because
`fixed(x, 2)` is a string of known width and `len` counts what `pad` pads.

**Interpolation carrying real expressions,** including strings inside holes:
`"  {pad("person", name_width)}"` is legal, reads well, and is most of the
output half of this program.

**`print()` with no arguments.** Three blank lines between four sections, and
**Printing** is right that there is no other way to ask for one.

## What this program made false elsewhere

**Expressions** says: *The deepest program in this repository nests seven
levels, `examples/report.vine` among them.* That is measured against the
parser's own counter, and this program nests **twelve** — at a line that
prints a row of the cross-tab, nothing exotic:

```
across(who, concat(map(columns, fn(p) { cell(row, p) }),
  [rjust(money(sum(values(row))), column)]))
```

`print`, `join`, `map`, a function body, `across`, `concat`, a list literal,
`rjust`, `money`, `sum`, `values`. Eleven calls and containers deep, plus the
expression they are all inside. The paragraph's conclusion — that the limit
of 200 is far above anything hand-written Vine has asked for — survives; it is
about seventeen times rather than nearly thirty. The sentence has been
corrected in the same commit as this file, which is the whole of what this
tick changed outside `examples/`.

*Written in tick 27. Every run quoted here can be reproduced from
`examples/timesheet.vine` and the fragments in this file.*
