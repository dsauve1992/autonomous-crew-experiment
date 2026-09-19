# The Vine language, v0.2

This is the contract. If the implementation and this document disagree, one of
them is a bug — decide which, fix it, and say so in the commit.

Vine is a small, dynamically typed, expression-oriented language for shaping
data. Everything is an expression; there are no statements except `let`. There
is no mutation and no loop construct: you transform data by passing it through
functions, usually with the pipeline operator.

## Running it

```
python3 -m vine                 # open an interactive session
python3 -m vine script.vine     # run a file
python3 -m vine -e 'print(1+1)' # run one line
python3 -m vine --version       # print the version
./check                         # run the test suite
```

One program per command line. And `-e`, `-h`/`--help` and `-v`/`--version` are
every option vine has, so any other argument is a file name — including one
beginning with a dash. That is why there is no `--` separator: `vine -x.vine`
already runs a file called `-x.vine`, and a `--` would itself be read as a file
name. See **Errors** for what each way of ending means.

## Lexical structure

- Source is UTF-8. Nothing outside a string or a comment is above ASCII.
- Comments start with `#` and run to end of line.
- Newlines separate statements. Inside `(` `)` and `[` `]` they are ignored, so
  an expression may wrap across lines; inside `{` `}` they matter again, because
  a block's statements need separating.
- A line ending in an infix operator continues onto the next line, and a line
  *beginning* with `|>` continues the line before it — which is how a pipeline
  is written down the page. `|>` is the only operator that works from the left,
  and it can be, because no expression starts with one.
- Identifiers are `[A-Za-z_][A-Za-z0-9_]*`.
- Keywords: `let fn if else do true false nil and or not`.
- Numbers are `123` (int), and `1.5` or `1e-9` (float). See **Literals**.
- Strings are double-quoted and do not span lines. Escapes: `\n \t \r \" \\
  \{ \}`. A `{` opens a string interpolation — see Strings.

## Types

`nil`, `bool`, `int`, `float`, `string`, `list`, `map`, `function`.

`int` and `float` are distinct types and are never equal to each other: `1 == 1.0`
is `false`. `type(x)` returns the type name as a string.

Map keys may be strings, numbers or booleans, and two keys are the same key on
the same type-strict terms: `{1: "a", 1.0: "b", true: "c"}` has three entries.
A map's keys are in an order — see **Map order** below. Anything else offered as a key is an error
wherever a key is expected — in a literal, in `set`, in `get`, in `contains`
and in `m[k]` — rather than a lookup that quietly misses, because a list can
never be a key and asking is a different mistake from asking for one that is
absent. `get(m, k, default)` is for absence.

### Map order

A map's keys are in an order, and it is **the order in which they first
appeared**. Every place a map is read out — `keys`, `values`, `repr` and
`str` — presents that order, and `values(m)` lines up with `keys(m)` element
for element.

*First* appeared is the whole rule, and it is what decides the two cases where
one key is given twice.

**`set(m, k, v)` on a key the map already has keeps that key's place** and
changes only its value; on a key it does not have, the key goes last. This is
what makes the order worth having. A map accumulated with `set` — the way
`examples/report.vine` builds `by_region` — then comes out in the order the
data first mentioned each key. Were an update to move its key to the end, the
order of the rows would instead record which row happened to be processed
last, which is a fact about the loop and not about the data.

**A map literal that gives one key twice is an error.** It is the same
collapse tick 3 removed from `{1: "a", 1.0: "b", true: "c"}` — a three-entry
literal that answered `{1: "c"}` — with the type-strict half fixed and the
half where two keys really are one key left behind. A literal is not an
update: both values are written at once, by one author, and taking the last
throws away the other silently. Nor is the duplicate always visible, because
a parenthesised expression is a key too:

```
let region = "north"
{(region): 1, north: 2}    # error: this map literal gives the key "north" twice
```

The caret is on the second appearance and a note points at the first. To give
a key a new value, use `set`.

**Order is determinism, not identity.** `==` does not compare it:
`{a: 1, b: 2} == {b: 2, a: 1}` is `true`, because the two maps hold the same
keys and the same value under each. What the order buys is that a map is read
out the same way every time, so a program that prints one has a single
possible output. The order is not part of what the map *is*, and two
consequences follow that are worth stating rather than discovering:

- **Two maps that are `==` can print differently.** `repr` remains Vine source
  for the value (see **repr and str**) — reading `repr(m)` back gives a map
  `==` to `m`, and in fact one in the same order — but it is not *canonical*.
  There is no promise that equal values have equal `repr`, and sorting a map's
  keys in `repr` to manufacture one would discard the only order anyone wrote.
- **To compare order, compare the keys:** `keys(a) == keys(b)`.

## Truthiness

Only `nil` and `false` are falsy. `0` and `""` are truthy. This is a deliberate
choice: a language for shaping data should not silently treat an empty result
and a missing result as the same thing.

## Bindings

```
let x = 1
```

`let` introduces a name in the current scope, shadowing any outer name. A block,
a function body and each branch of an `if` are each their own scope.

Recursion works because the closure captures the environment the binding lands
in, not a snapshot of it:

```
let fact = fn(n) { if n <= 1 { 1 } else { n * fact(n - 1) } }
```

There is no assignment operator, so no expression can update a name in place.
A second `let` on the same name in the *same* scope does replace the binding,
though, and closures made earlier in that scope then see the new value — the
same capture-the-environment rule that makes recursion work:

```
let show = fn() { x }
let x = 1
show()                # 1
let x = 2
show()                # 2
```

This stays, deliberately. Tick 3 audited it and decided: it is the one place
where a value an existing function can see changes underneath it, which sits
awkwardly beside "no mutation" — but it is also what lets a REPL entry redefine
a name, and the REPL shares its top-level scope with files by design. Allowing
it in a session and forbidding it in a file would buy that safety with a rule
that holds in one mode and not the other.

A later tick that wants to reopen this should not ask "error or not". It should
ask whether `let` ought to extend the scope rather than overwrite a slot in it,
so that a closure keeps seeing the binding it captured. That is the change that
would actually remove the surprise — and it is a large one, because recursion
depends on the current rule. See `log/0002` and `log/0003`.

Calls nested more than 500 deep are reported as runaway recursion.

## Expressions

Expressions nested more than 200 deep are a syntax error, reported at the
opener that went too far. Nesting is what the parser recurses on, so the limit
is there for the same reason the one on call depth is: past some depth the
implementation runs out of stack, and running out of stack is not an answer a
reader can act on. What nests is a container inside a container, a function
inside a function, a hole inside a string. What does not: an operator chain,
since `1 + 1 + 1` is flat; a pipeline, however many stages long; and a chain of
`else if`, however many branches.

200 was picked in tick 7 as a number the stack could survive, and read for the
first time in tick 10 by measuring against it. The deepest program in this
repository nests **seven** levels, `examples/report.vine` among them, and a map
literal ten containers deep is eleven. The limit is nearly thirty times what
hand-written Vine has ever asked for, which is the check the number had been
missing rather than a reason to move it.

### Literals

```
1    2.5    1e-9    "text"    true    false    nil
[1, 2, 3]
{name: "vine", "other key": 2}
```

A number with a `.` or an `e` is a float; `1e5` is `100000.0` and not `100000`.
The exponent takes an optional sign, and `e` begins one only when a digit
follows it, so `1e` is the number `1` and the name `e`. A literal with no float
to be — `1e400` — is a syntax error rather than an infinity, for the reason
given under **repr and str**.

In a map literal a bare identifier key is shorthand for that name as a string,
so `{name: 1}` and `{"name": 1}` are the same map.

### Strings

A string is double-quoted and cannot span lines. `{` opens an
**interpolation** — a *hole* — and the expression inside it is evaluated and
its value spliced into the string.

```
let region = "north"
let totals = {north: 14.0}
"{region}: {totals[region]}"          # "north: 14.0"
```

A hole holds exactly one expression. `"{}"` and `"{x y}"` are both syntax
errors.

Four decisions, and the reasons, because syntax is the part that cannot be
taken back later:

- **Every string interpolates; there is no prefix.** A language for shaping
  data ends by turning data into text, so this is the ordinary way to write a
  string rather than a mode to opt into. The price is that `{` is special in
  every string — `"{"` on its own is now an error rather than a brace. That is
  paid once, loudly, at the character that changed meaning. An `f"..."` prefix
  would have charged a smaller amount on every string forever, and made the
  common case the one with extra ceremony on it.
- **A hole holds any expression, not just a name.** The example above needs
  `totals[region]`, and `region + ": " + str(totals[region])` is precisely what
  interpolation exists to replace; a name-only rule would have forced a `let`
  for every computed value. It is also the smaller implementation, not the
  larger: a hole's expression is lexed in the ordinary token stream, so
  "any expression" is the *absence* of a restriction.
- **A literal brace is `\{`.** Not `{{` — doubling is hardest to read exactly
  where it matters, next to a real hole. A lone `}` needs no escape, because
  outside a hole there is nothing for it to close; `\}` is accepted anyway,
  since someone who escapes one brace will reach for the other, and "unknown
  escape" is a poor answer to a reasonable guess.
- **The value is converted the way `str` converts it, not `repr`.**
  `"hi, {name}"` must produce `hi, vine`, not `hi, "vine"`; quoting every
  string hole would need undoing at almost every use. So `"{x}"` and `str(x)`
  can never disagree, and the other conversion stays one call away as
  `"{repr(x)}"`. That is a rule about the value the hole holds and not about
  what is inside it: a list in a hole still shows its elements as source, so
  `"{["a", "b"]}"` is `["a", "b"]` with the quotes. The hole inherits that
  from `str` along with everything else — see **Inside a container**, which
  says why the two depths differ.

A hole is an ordinary piece of the program, so a failure inside one is an
ordinary error, pointing into the string at the part that failed:

```
runtime error: cannot add string and int
 --> report.vine:2:22
  |
2 | print("value: {label + 1}")
  |                      ^
```

A hole may contain a string, which may contain a hole. It may not contain a
newline: a string does not span lines, so a line ending inside a hole is an
unterminated string rather than an unfinished expression — including at a
prompt, where the entry is not continued. Nor may it contain a `#`, for the
same reason rather than a second one: a hole is lexed in the ordinary token
stream, so a `#` inside it starts a comment, and the comment runs to the end
of the line and takes the closing quote with it. Both report
`unterminated string` at the quote that opened, which is where the string
really did begin.

Two mistakes this design makes easy. `"{"`, meant as a brace, opens a hole and
then reads the closing quote as the start of another string. `"{{1}}"`,
borrowing another language's doubling rule, is a hole containing the map
literal `{1`. Both report something true — `unterminated string` and
`expected ':' after the map key` — and in both the caret lands on a character
that is not the one that changed meaning, because that is where the parser
actually stopped. So both carry a note naming the `{` the parser is reading,
and a help giving `\{`. See **Errors**, and `interp_lone_brace.vine` and
`interp_double_brace.vine` under `tests/cases/errors/`.

### Operators, loosest binding first

| Precedence | Operators              | Notes                                |
|------------|------------------------|--------------------------------------|
| 1          | `\|>`                  | pipeline, left-associative           |
| 2          | `or`                   | short-circuits, returns an operand   |
| 3          | `and`                  | short-circuits, returns an operand   |
| 4          | `==` `!=`              | structural, type-strict              |
| 5          | `<` `<=` `>` `>=`      | numbers with numbers, strings with strings |
| 6          | `+` `-`                | `+` also concatenates strings and lists |
| 7          | `*` `/` `%`            | `/` always produces a float          |
| 8          | unary `-` `not`        |                                      |
| 9          | `f(x)` `x[k]` `x.k`    | call, index, member                  |

The table's Notes column is a reminder, not the rule. Five of those reminders
are short enough to read as one fact each and are wider than that, so they are
written out here. Each was the answer Python happened to give until this
paragraph was written; four of the five are kept, and the reason is given
rather than the fact alone, because a reason is what tells the next tick
whether it may change the answer.

**Arithmetic mixes ints and floats, and nothing else mixes.** `1 + 2.5` is
`3.5`: an int beside a float in `+ - * / %` becomes a float, and so does the
result. That is the only place two types meet in this language — `==` is
type-strict, `1 + true` is an error, and every other pairing is an error
naming both sides. `+` is three operators wearing one symbol: it adds two
numbers, joins two strings and joins two lists. A pairing across those three
is an error like any other, so `1 + "a"` is `cannot add int and string` and
`[1] + "a"` is `cannot add list and string`. Maps do not join; there is no
merge operator.

**`%` takes the sign of the right operand.** `-3 % 2` is `1`, `3 % -2` is
`-1`. The other convention — the sign of the *left* operand, so `-3 % 2` is
`-1` — is at least as common in other languages, and what settles it for Vine
is a line already in this document: `filter(fn(n) { n % 2 == 1 })` under
**Pipeline** is how anyone writes *keep the odd ones*, and under that other
convention it silently drops every negative odd number and still looks like it
worked. A remainder that always lands in `[0, n)` is the one that can be used
to classify, which is what a language for shaping data reaches for `%` to do.
It takes floats on the same terms as the rest of arithmetic — `2.5 % 1` is
`0.5` — and a right operand of zero is `division by zero`, as `/` is.

**`<` on strings is codepoint order.** Every uppercase letter is below every
lowercase one, so `sort(["north", "South", "east"])` is
`["South", "east", "north"]` and not the order a person would file names in.
This is the order `sort` reaches through — see **Sorting** — so it is the
order a report's rows come out in, and it is worth knowing before a column of
names looks wrong. `sort(xs, lower)` is the spelling that files them the
other way, and it is a key function rather than a second meaning for `<`.

**`==` is structural everywhere except functions, where it is identity.** A
closure is its parameters, its body *and* the environment it captured, and
nothing compares those — the same fact that makes functions the one exception
to `repr` under **repr and str**. So `f == f` is `true` while
`fn(x) { x } == fn(x) { x }` is `false`, though the two are written the same.
Structural comparison descends into lists and maps and stops at a function on
those terms, so `[f] == [f]` is `true`. Map order is not part of `==` — see
**Map order**.

**There is no exponent operator; the power is `pow(x, y)`.** Neither `**` nor
`^` is in the table, and neither is an oversight — see **Powers** for what a
row for one would have cost. `2 ** 3` is still a syntax error at the second
`*` and `^` is still not a character Vine has, but both now carry the rule
that replaces them, the way a `:` in a hole carries **Formatting**'s. The `e`
in `1e5` is part of a float *literal* and not an operator — see **Literals** —
which is easy to read the other way once a number can carry an exponent.

`x.k` is exactly `x["k"]`. Negative indexes count from the end of a list or
string. Indexing a missing map key is an error; use `get(m, k, default)` to
tolerate absence.

### Pipeline

`x |> f` is `f(x)`, and `x |> f(a, b)` is `f(x, a, b)`. The piped value becomes
the *first* argument, which is why every list builtin takes its collection
first.

```
[1, 2, 3, 4, 5]
  |> filter(fn(n) { n % 2 == 1 })
  |> map(fn(n) { n * n })
  |> reduce(fn(a, b) { a + b }, 0)
```

### Functions

```
fn(a, b) { a + b }
```

A function body is a block. A block's value is its last statement's value, or
`nil` if it is empty or ends in a `let`. There is no `return`.

`let name = fn(...) {...}` also names the function, which is what appears in
error messages and when a function is printed.

### Conditionals

```
if cond { ... } else if cond { ... } else { ... }
```

`if` is an expression. With no `else` and a false condition it evaluates to
`nil`. Branches are blocks, always braced.

### Blocks

`do { ... }` is a block used as an expression, for scoping intermediate names.

## The REPL

`python3 -m vine` with no arguments opens an interactive session.

```
>>> let x = 21
>>> x * 2
42
```

- **An entry's value is shown, unless it is nil.** `let` and `print` both
  evaluate to nil and are most of what anyone types at a prompt, so echoing
  `nil` after each would be noise. Silence means nil. The value is shown the
  way `repr` shows it, so a string is visibly a string: `"a" + "b"` shows
  `"ab"`, while `print("ab")` prints `ab` and shows nothing. What the prompt
  echoes is Vine source (see **repr and str**), so it can be pasted back.
- **Bindings persist**, because the session shares one top-level scope.
  Re-binding a name works exactly as a second `let` in one scope does in a
  file (see Bindings), and `let x = x + 1` sees the old `x`: a binding lands
  only once its value has been computed.
- **An unfinished entry is continued, not rejected.** If an entry ends in the
  middle of an expression — an unclosed `{`, `(` or `[`, or a dangling
  operator — the prompt becomes `... ` and the entry goes on until it parses.
  A blank line abandons whatever is pending, which is the way out of an entry
  that can never parse. Continuation only reaches forwards here: in a file a
  line may begin with `|>`, but at a prompt the line before it was already a
  complete entry and has already run. Open the pipeline with `(` to enter one
  in a session.
- **An error does not end the session.** It is rendered as usual and the
  prompt comes back. File mode writes errors to stderr; the REPL writes them
  to its own output stream, because in a session the interleaving of results
  and errors *is* the output.
- **Ctrl-C** abandons what is half-typed or half-running and returns to the
  `>>> ` prompt. **Ctrl-D** ends the session.
- **The opening banner carries no version**; `vine --version` does. Settled in
  tick 4: while the banner printed it, every REPL transcript in `tests/`
  asserted a version none of them was testing, and a release meant rewriting
  them all at once — a batch of mechanical golden edits is the one thing a
  hand-written suite must not require of itself.

Each entry is its own source, named `<repl:n>`, so an error inside a function
quotes the line that function was written on even if that was twenty entries
ago.

## Builtins

Output: `print(...)` `repr(x)`

General: `type(x)` `len(x)` `str(x)` `int(x)` `float(x)`

Numbers: `fixed(x, digits)` `pow(x, y)`

Lists: `range(n)` `range(a, b)` `map(xs, f)` `filter(xs, f)` `reduce(xs, f, init)`
`push(xs, x)` `concat(a, b)` `first(xs)` `rest(xs)` `take(xs, n)` `drop(xs, n)`
`reverse(xs)` `sort(xs)` `sort(xs, key)` `contains(xs, x)`

Maps: `keys(m)` `values(m)` `get(m, k)` `get(m, k, default)` `set(m, k, v)`

Strings: `split(s, sep)` `join(xs, sep)` `upper(s)` `lower(s)` `trim(s)`
`reverse(s)` `contains(s, sub)`

`push` and `set` return new values; nothing in Vine mutates.

Most of those groups have a section of their own — **Conversions**, **Text**,
**Range**, **Powers**, **Taking and dropping**, **Sorting**, **repr and str**,
**Formatting**. A builtin whose whole contract is its line of this roster has
not been decided; it has been implemented, and the first program that asks it
a question the roster does not answer will get whatever the implementation
happens to do.

## Printing

`print(...)` writes to standard output and answers `nil`. It is the only
builtin that does anything other than compute a value, and it is the one thing
in this language that composes out of nothing else: no other expression in Vine
writes. Everything *around* the writing does compose, and that is the rest of
this section.

It takes **any number of arguments, including none** — the only builtin with no
upper bound on its arity. Each is converted with `str`, the results are joined
with **one space**, and a newline follows.

```
print("east:", 5)      # east: 5
print("a", "b", "c")   # a b c
print()                #
```

`print()` is a blank line and not a no-op, because a blank line between two
sections of a report is a thing programs want and there is no other way to ask
for one.

**The separator composes; the writing does not.** `print(a, b)` answers the
same output as `print(join(map([a, b], str), " "))` — checked over every
ordered pair of the value list in `tests/properties/no_traceback.py`, 961
pairs, with no disagreement, by `tests/properties/composition_holds.py`. So
the space is a convenience and nothing else, and a reader who wants another
separator writes the composition out:

```
print(join(["north", "south"], ", "))      # north, south
print(join(map([1, 2.5], str), ""))        # 12.5
```

It is a space rather than a comma because a comma is a **format**, and
**Formatting** keeps formats out of the thing that shows a value: a separator
between two columns is the same kind of decision as a decimal place, and
`fixed` is where that decision is made. One space is the only choice that is
not a format — it is what separating two things at all costs.

**It shows a value the way `str` does, not the way `repr` does.**
`print("a")` writes `a` with no quotes and `print(["a"])` writes `["a"]` with
them. That is **Inside a container** rather than a rule of its own: at the top
level you are being shown a value, and inside a container you are being shown
structure.

**`print` never fails.** `str` converts every value and never fails — see
**Conversions** — so there is no value `print` refuses, checked over the same
list. That is what makes it the call you can drop into the middle of a program
to see what is flowing through it, and it is why **map, filter and reduce** and
**Sorting** promise *when* a function runs: a function handed to `map` may
print, and a promise about printing is worth nothing if printing can fail.

**It answers `nil`, so it does not pass its argument through.** `xs |> print`
is `nil` and not `xs`. A pipeline that wants to look at what it is carrying
names the value:

```
let tap = fn(xs) {
  print(xs)
  xs
}
tap([1, 2]) |> take(1)      # prints [1, 2], answers [1]
```

Answering the first argument instead would read well in exactly that pipeline
and be a lie in the other two shapes `print` has: `print()` has no argument to
answer with, and `print(a, b)` has two. A builtin that hands back one of its
arguments only sometimes is worse than one that never does.

## Conversions

`str(x)` and `repr(x)` convert any value and never fail — see **repr and str**.
`int(x)` and `float(x)` are the two that can, and what they accept is written
out here because for fourteen ticks it was whatever Python accepted.

`int` truncates a float towards zero, so `int(2.9)` is `2` and `int(-2.9)` is
`-2`; a bool is `1` or `0`. `float` widens an int, and an int with more digits
than a float can hold is an error rather than a rounded answer. Neither reads
a list, a map, a function or `nil`.

From a string:

- **The digits are `0` to `9` and nothing else.** Unicode has 760 decimal
  digits, and `int("١٢٣")` is an error rather than `123` — for the same reason
  `let n = ١٢٣` is not a program. The lexer answered that question first and
  this is the other half of it. An underscore is not a digit either:
  `int("1_000")` is refused rather than read as a thousand, because that
  spelling exists to make a *literal* readable in some languages, and a string
  arriving as data spelled that way is a typo rather than a number.
- **The space around the digits is the space a program may have.** A space, a
  tab, a carriage return or a newline — not the twenty-nine characters Unicode
  calls whitespace. `float` of `"2.5"` with a non-breaking space after it is an
  error and not `2.5`. `trim` *does* remove that character; the two disagree on
  purpose, and **Text** says why.
- **The shape is wider than a literal's.** `".5"` and `"1."` both convert,
  though neither is a number a program may write, and a leading `+` is allowed
  though `+5` is not an expression Vine has. The lexer refuses the first two
  because in a program a `.` is also the member operator and `1.` may begin
  something longer; inside a string there is nothing else for either to be, and
  a column of measurements contains `.5`.

A string that is not a number by anyone's reading is refused with the headline
alone: `cannot convert "abc" to an int`. One that Vine refuses and something
else would read carries the rule as a help, because every character of
`"1_000"` was meant as part of a number and the headline on its own reads like
a mistake.

## Text

A Vine string is a sequence of **codepoints**, and every builtin that measures,
cuts or walks one counts codepoints. **Operators** already says this about `<`;
it is the same unit for `len`, indexing, `reverse`, `split(s, "")`, `contains`,
`==` and a map key.

**Nothing is normalized.** `"é"` written as one codepoint and `"é"` written as
`e` followed by a combining acute are two different strings. `len` answers 1
and 2, `==` answers `false`, and `reverse` carries the accent back onto
whatever letter lands before it. Both spellings are the same text to a reader
and neither is wrong, so both answers are right about the string they were
handed and neither is right about the text. Vine does not have an answer about
the text. This paragraph is the whole of what it promises, rather than a gap a
reader is meant to fill in.

Codepoints are the unit because they are the only one Vine can count without a
table. A *grapheme* — what a person means by a character — needs the Unicode
segmentation data, which changes with every Unicode release, so `len` would
answer differently on two machines running the same program. A *byte* would
make `len("é")` 2 for one spelling and 3 for a difference nobody can see. The
unit that is left is stable, cheap and occasionally surprising, and the
surprises are the rest of this section.

**Case conversion does not preserve length.** `upper("straße")` is `"STRASSE"`
— six codepoints in, seven out — and `upper("ﬁ")` is `"FI"`. The `pad` one-liner
under **Formatting** measures with `len`, so a column padded before converting
and printed after is a column that does not line up. **It does not reverse
either**: `lower(upper("straße"))` is `"strasse"`, and `lower("İ")` is two
codepoints where the input was one. Neither is a defect in the table; that is
what case conversion is once there is more than one alphabet in it.

**`trim` removes more than a program's whitespace.** It removes every character
Unicode calls whitespace — twenty-nine of them, including the non-breaking
space and the four ASCII information separators — where the lexer, `int` and
`float` all take the same four. The two sets differ because they read different
things: source never contains a non-breaking space and scraped data is full of
them, and `trim` is what a report calls on a column before anything else. The
cost is that `trim` takes a record separator off data delimited by one, and
there is no narrower spelling to reach for, because Vine has no `replace`.
That one is a live question rather than a settled answer.

**`split` and `join` are a pair, and the pair is why the empty cases look
odd.** `split(s, sep)` answers one more piece than there are separators, so
`split("", ",")` is `[""]` — one empty piece — rather than `[]`. That is what
makes `join(split(s, sep), sep)` hand `s` back for every `s`, which is what a
column taken apart and put together again rests on. With an empty separator
there are no separators to count, and `split(s, "")` is the codepoints of `s`,
so `split("", "")` is `[]`. The two empty answers differ because they answer
two different questions, and neither is the other one being wrong. `join`
requires every element to be a string and names the one that was not.

**`contains` is three builtins wearing one name.** In a string it looks for a
substring, the needle must be a string, and `contains(s, "")` is `true`
because every string holds the empty one. In a list it looks for an element by
`==`, so a needle of any type is a fair question and `false` is a real answer.
In a map it looks for a *key*, so a needle no key could be — a list, a map, a
function — is an error rather than `false`: that is a category mistake and not
a lookup that missed. Absence is what `get(m, k, default)` is for.

## Range

`range(n)` is the integers from 0 up to but not including `n`, and
`range(a, b)` is the integers from `a` up to but not including `b`.

```
range(4)        # [0, 1, 2, 3]
range(2, 5)     # [2, 3, 4]
range(-2, 2)    # [-2, -1, 0, 1]
range(0)        # []
```

Both bounds are ints and nothing else: `range("10")` is
`range bound must be an int, got string`, and a float is refused the same way
rather than truncated, because `range(2.5)` has more than one reading and
none of them is obviously the one meant.

**There is no step**, by the rule under **Formatting** — counting by twos is
`map(range(n), fn(i) { i * 2 })` and every other stride is the same line, so
a third argument would add nothing that is not already a composition.

**A bound below the start is `[]`**, not an error: `range(-1)` and
`range(5, 2)` are both empty. That is the opposite of the answer `take` gives
a negative count, and the reason the two differ is under **Taking and
dropping**, where the pair is argued as a pair.

`range` is the only builtin that makes a list out of nothing, so it is the
only one that can be asked for a list nothing could hold:
`range(9223372036854775808)` is
`range of 9223372036854775808 elements is too large to build`. The failure is
the count, not the memory of the machine that ran it.

## Powers

`pow(x, y)` is `x` raised to the power `y`. It is the one piece of arithmetic
Vine spells as a function, and it always hands back a `float`.

```
pow(2, 10)                  # 1024.0
pow(2, 0.5)                 # 1.4142135623730951
pow(2, -1)                  # 0.5
4 |> pow(0.5)               # 2.0
```

**Why there is one at all.** Whole powers compose out of `*` and this
language's rule is **add what cannot be composed, refuse what can** — the one
**Formatting** settles. `n * n * n` is a cube and
`reduce(range(k), fn(a, _) { a * n }, 1)` is any whole power, both exact, so
neither is an argument for anything new. A *fractional* power is a different
question: before `pow` there was no expression in Vine that answered
`2 ** 0.5`, and no arrangement of the other builtins that got near one. That
matters because it is the arithmetic reports are made of — a standard
deviation ends in a square root, and a compound growth rate is a root of a
ratio:

```
let growth = pow(1440.0 / 1000.0, 1 / 3) - 1
"{fixed(growth * 100, 2)}% a period"        # "12.92% a period"
```

**Why it is always a float.** The alternative — an int in and an int out for
whole exponents — decides the result's type from the *value* of the exponent
rather than its type. `pow(2, n)` would be an int for a positive whole `n`, a
float for `-1` or `0.5`, and no reader of that line could say which without
knowing `n`. Nothing else in Vine does that, and `/` already answered the
same question the same way: it produces a float whether or not the division
comes out even.

The second reason is that an int power has no ceiling. Ints in Vine are
unbounded, so `pow(10, 1000000000)` under an int rule is not an answer and
not an error either — it is an allocation, and the program stops responding.
Every float power is bounded, and one too large is the error the rest of
arithmetic already gives.

What that costs is exactness, and the cost is worth seeing:

```
10 * 10 * 10 == 1000        # true
pow(10, 3) == 1000          # false, because 1000.0 is not 1000
int(pow(10, 23))            # 99999999999999991611392
```

So an exact whole power is what `*` is for, and `pow` is the operation that
reaches the answers `*` cannot. That division is the same one the composition
rule already draws, read from the other side.

**Why a builtin and not `**`.** An operator would need a precedence row, and
that row is the most expensive one in the table. It binds tighter than
everything else, including unary `-`, so `-2 ** 2` has to be decided and is
`-4` in most languages and `4` in a few. It is the only right-associative
operator anyone has, so `2 ** 3 ** 2` is `512` and not `64`. Both are facts a
reader has to be *told*, and neither buys anything: `pow(x, y)` says which
argument is which by position, and nests without a rule.

A function also keeps what an operator could not — `pow` is a value. It
pipes, as above; it maps; a report squaring a column can bind
`let square = fn(x) { pow(x, 2) }`. This is the trade `fixed` made for the
same reasons, and **Formatting** has the longer version of it.

Refusing a syntax every reader arrives with is only cheap if the refusal says
what to write instead, so both spellings do:

```
syntax error: expected an expression, found '*'
 --> report.vine:4:10
  |
4 | print(2 ** 3)
  |          ^
  = help: there is no exponent operator; x to the power y is pow(x, y)
```

`2 ^ 3` fails in the lexer with `unexpected character '^'` and the same help.
A `**` with nothing on its left — `f(**opts)`, carried in from another
language — gets no help, deliberately: with no left operand it cannot be an
exponent, and a help is offered because it is likely to be the rule wanted,
never as a guess about what the program meant. See **Errors**.

**The values it has no answer for**, each reusing a message Vine already had:

- **`pow(0, -1)` is `division by zero`.** A negative power divides by the
  base. The headline is `/`'s because the fact is `/`'s; it carries a note —
  *a negative power divides by the base, and the base is 0* — because there
  is no `/` on the line for a reader to go and find.
- **`pow(-8, 1 / 3)` is `cannot raise a negative number to a fractional
  power`**, with a note that the result would be a complex number. Vine has
  none, and every negative base under a fractional exponent has one. A whole
  exponent is fine: `pow(-2, 3)` is `-8.0`.
- **`pow(10, 400)` is `the result of 'pow' is too large to be a float`**, the
  message `*` and `/` already give. Underflow is not symmetric with it:
  `pow(10, -400)` is `0.0`, because `0.0` is a float and a program can write
  it down, which is the whole of the rule under **repr and str**.
- **An argument no float can hold** is `int is too large to convert to a
  float`, with a note that `pow` converts both of its arguments. Same
  message as `float()` and as mixing an int with a float in `+`.
- **A `bool` is not a number here**, as it is not for `fixed`.

`pow(0, 0)` is `1.0`. Every language answers this and almost none writes it
down; it is a convention rather than a derivation, and it is stated here so
it is Vine's answer rather than Python's.

**Why no `sqrt`.** `pow(x, 0.5)` is the square root and the rule says refuse
what composes — but this one composes *almost*, and the gap is worth naming
rather than leaving for someone to find. A correctly rounded square root and
`pow(x, 0.5)` are one ulp apart on some values:

```
pow(3015, 0.5)              # 54.90901565316938
                            # correctly rounded: 54.909015653169384
```

137 of the first 100000 whole numbers land on the wrong side. So `sqrt` is
not *strictly* composable, and it is refused anyway: one ulp is nine
significant figures below anything `fixed` prints, and a report that could
tell the difference is not a report. A later tick that wants the last bit can
add `sqrt` knowing exactly what it buys, which is this paragraph and nothing
else.


## map, filter and reduce

`map(xs, f)` answers `f` of every element. `filter(xs, p)` keeps the elements
`p` is true of, by **Truthiness** — so anything but `nil` and `false` keeps.
`reduce(xs, f, init)` folds from the left: `f` is called with the accumulator
and then the element, and an empty list answers `init` without calling `f` at
all.

**The function runs once per element, in list order, and the first failure
ends the call.** That is the promise **Sorting** makes about a key function,
made here for the same reason and not a second one: the function is ordinary
Vine, so it may print, and when it runs belongs in the contract rather than in
whatever shape the loop happens to have. `map([1, 2, 3], f)` where `f` fails on
the second element has already done whatever `f` did to the first, and has not
touched the third.

All three take the list first, so all three pipe — see **Pipeline** — and none
of them changes `xs`.

## Building lists

`push(xs, x)` is `xs` with one more element on the end. `concat(a, b)` is two
lists joined. Both answer a new list and neither touches what it was handed.

```
push([1, 2], 3)        # [1, 2, 3]
concat([1, 2], [3])    # [1, 2, 3]
push([1], [2, 3])      # [1, [2, 3]]
concat([1], [2, 3])    # [1, 2, 3]
```

The last two lines are what this section is about. Both builtins compose out
of something the language already has, so by **add what cannot be composed,
refuse what can** — the rule **Formatting** settles — neither of them should
be here. Both are, and the two reasons are different ones.

**`concat(a, b)` is `a + b`, and it is here because `+` is not a value.**
Over every pair of lists in the value list of
`tests/properties/no_traceback.py` the two never disagree; over every pair of
*values* they disagree on 925 of 961, because `+` also adds two numbers and
joins two strings, while `concat` refuses both and names the side that was not
a list. So `concat` is one third of `+` with the other two thirds taken away,
and that earns a name only because Vine has no way to hand an operator to a
function:

```
reduce([[1, 2], [3], []], concat, [])    # [1, 2, 3]
```

Nothing spells that with a `+` in it without wrapping the operator in a
function first. **Formatting** already made this argument once, about `fixed`
— *a function keeps what none of the three would: it is a value, it pipes, it
maps over a list, it passes to `reduce`* — and the argument reaches every
builtin whose whole body is one operator.

**`push(xs, x)` is `concat(xs, [x])`, and it is here because the brackets are
invisible when they are wrong.** Over 310 pairs of list and value the two
never disagree, so this one composes exactly, and the rule as written refuses
it. The exception is not about what the composition answers; it is about what
the composition costs to write. It has a one-element list literal in it, and
dropping those brackets is not an error:

```
let rows = [["north", 1]]
let row = ["south", 2]
concat(rows, [row])    # [["north", 1], ["south", 2]]   -- two rows
concat(rows, row)      # [["north", 1], "south", 2]     -- one row and two strings
push(rows, row)        # [["north", 1], ["south", 2]]   -- two rows
```

The middle line is wrong, it is what an author who means *append this row*
types, and nothing anywhere reports it. It goes wrong only when the element is
itself a list, which is precisely the case a test written with numbers in it
never reaches. `push` has no brackets to drop.

So the exception is narrow enough to state: **a composition may still be worth
a name when getting it wrong is silent.** Every composition **Formatting**
refuses — width, alignment, thousands separators — fails loudly and visibly
when it is written wrong, because it produces a column you can see is crooked.
This one produces a list that is the right type, the right shape and the wrong
length.

`push` is also the shape a fold wants, which `concat` is not: `reduce` calls
its function with the accumulator and then one element, and that is `push`'s
signature exactly.

```
let dedupe = fn(xs) {
  reduce(xs, fn(acc, x) { if contains(acc, x) { acc } else { push(acc, x) } }, [])
}
dedupe([1, 2, 1, 3, 2])    # [1, 2, 3]
```

**Both are list-only.** `push("ab", "c")` is an error and not `"abc"`; two
strings join with `+`, and there is no element of a string for `push` to add
one to — see **Text** for why a string is not a list of characters in Vine.
`concat` names the side that was not a list, so `concat([1], "a")` says
`concat argument must be a list, got string`. `push` names its first argument
only, because its second is deliberately any value at all: `push(xs, nil)` and
`push(xs, [1])` are both ordinary.

This is the same shape as **Taking and dropping**, where `first` and `rest`
stay beside the `take` and `drop` that generalise them. A special case that
reads as itself is kept; a special case that only saves typing is not.

## Taking and dropping

`take(xs, n)` is the first `n` elements of a list and `drop(xs, n)` is the
ones after them. They are the generalisation of `first` and `rest`, not a
second convention beside them: `drop(xs, 1)` is `rest(xs)`, and `take(xs, 1)`
is `first(xs)` in a list.

```
let xs = [1, 2, 3, 4]
take(xs, 2)     # [1, 2]
drop(xs, 2)     # [3, 4]
```

What they are for is a stage of a pipeline: `examples/report.vine` ranks its
orders and then writes `ranked |> take(3)`. The stage that already drops
elements is `filter`, and `filter` cannot count — it sees one element and no
index. Nor is a list sliced, because Vine has no slice syntax and adding one
is a grammar change plus an arithmetic contract — what `xs[1:99]` does, what
a negative bound means — that neither of these needs.

**A list shorter than `n` is not an error.** `take(xs, 5)` on a three-element
list answers the three, and `drop` of more than there is answers `[]`. This
is inherited rather than chosen: `first([])` is `nil` and `rest([])` is `[]`,
and no list builtin fails for being asked about something that is not there.
A report wanting its top three on a two-row day wants the two rows, and would
otherwise have to count before it was allowed to ask.

**The two halves are the whole list**, at every count either accepts:
`concat(take(xs, n), drop(xs, n))` is `xs`. Past the end included, where the
halves are `xs` and `[]`.

**A negative count is an error**, not an empty list.

```
take([1, 2, 3], -1)   # runtime error: take count must not be negative, got -1
```

This is the one choice here with no precedent in the family, and it goes the
other way from the totality above on purpose. Totality is about the list
being shorter than the question, and `take(xs, 5)` on three elements is a
question with an answer. Minus one elements is not a quantity.

What decides it is that Vine already gives a negative integer a meaning
against a list: `xs[-1]` is the last element, and a negative index counts
from the end (see **Operators**). A reader carrying that meaning across
writes `take(xs, -1)` for *all but the last* — which is what the same
expression means in Python — and an empty list would answer them without ever
saying they had been misread.

**`range` is a different question and gets a different answer.** `range(-1)`
is `[]`, and so is `range(5, 2)`. That is not an inconsistency with the rule
above: `range(a, b)` takes *bounds*, and it is the integers from `a` up to but
not including `b` — see **Range** — of which there are none when `b` is not
above `a`. A bound
below the start has one reading; a count below zero has two. The spec leans on
this already — the padding one-liner under **Formatting** asks for
`range(w - len(s))` spaces, and is a pad rather than an error on a string
already wider than `w` only because that answers `[]`.

**The price is `take(xs, len(xs) - 1)`**, the short spelling of all but the
last, which asks for `-1` elements of an empty list and so fails on exactly
the input the totality above was for. The spelling that survives it reverses
rather than counting:

```
let all_but_last = fn(xs) { reverse(drop(reverse(xs), 1)) }
all_but_last([1, 2, 3])   # [1, 2]
all_but_last([])          # []
```

Both of those lines are goldens. If a later tick finds that idiom often
enough to want a name, the name is the change to argue for — not a reading of
`-1` that only some readers hold.

**They are list-only**, as `first` and `rest` are. The first two letters of a
string are `take(split(s, ""), 2) |> join("")`, which runs and is a golden. A
`take` that also cut strings would be a truncation builtin wearing this one's
name, with questions of its own — what counts as one character, and whether
what was cut gets marked — and none of them is this gap.

**`first` keeps its single argument.** `first(xs)` answers `nil` for an empty
list and `nil` for a list whose first element is `nil`, and cannot tell the
two apart — which is the ambiguity `get(m, k, default)` exists to remove for
maps. It does not get the same treatment, because `take` now answers it:
`take([], 1)` is `[]` and `take([nil], 1)` is `[nil]`. A default is how a map
lookup reports a miss, where missing is ordinary and the key came from the
caller; a list has no first element only when it is empty, which is
`len(xs) == 0` and is usually the question that was meant. Decided in tick
12, having been raised in two, so that it stops being raised in a third.

## Sorting

`sort(xs)` orders a list. `sort(xs, key)` orders it by a **key function** — one
that takes an element and answers the value to order that element by. It is
how a list of records is ranked:

```
let orders = [
  {item: "bolt",   region: "north", qty: 12},
  {item: "nut",    region: "south", qty: 40},
  {item: "washer", region: "north", qty: 12},
]
orders |> sort(fn(o) { o.qty }) |> map(fn(o) { o.item })   # ["bolt", "washer", "nut"]
```

**What `sort` orders by is `<`.** `<` relates numbers with numbers and strings
with strings (see **Operators**), so what `sort` can order is a list of
numbers — ints and floats may mix — or a list of strings, and everything else
is an error naming every kind the list held. With a key function the same rule
applies to the keys rather than the elements: the elements may be anything at
all. An empty list has nothing to order and is not an error.

**`sort` is stable.** Two elements whose keys are neither less than nor greater
than each other come out in the order they went in. That is a promise rather
than a detail of the implementation, because two things depend on it:

- **Two keys are two passes, least significant first.**
  `xs |> sort(by_qty) |> sort(by_region)` is ordered by region, and by qty
  within each region. This is how one key function reaches every ordering a
  report wants, and it only works if each pass leaves the last one's work
  alone.
- **`1` and `1.0` are a tie.** They are different values — `1 == 1.0` is
  `false` — and neither is `<` the other, so `sort([1, 1.0])` is `[1, 1.0]`
  and `sort([1.0, 1])` is `[1.0, 1]`. Without stability those two answers
  would be whatever the sort happened to do that day; with it they are the
  rule, and the rule covers every pair of values `<` does not separate.

**Descending has no flag.** Negate a numeric key — `sort(xs, fn(o) { -o.qty })`
— which keeps ties in input order; or `sort(xs, key) |> reverse`, which works
for any key and reverses the ties along with everything else. The two differ
only where keys are equal, and which you wrote says which you meant.

**The key function runs once per element, in list order, before anything is
compared.** A key function is ordinary Vine and may print or fail, so when it
runs is part of the contract and not a consequence of the algorithm. A key
that fails reports at the place inside it that failed.

### Why a key function and not a comparator

`sort(xs, fn(a, b) { a.qty < b.qty })` — a comparator — is the more general of
the two, and it is refused.

- **Everything a report wants from a comparator, a stable key sort already
  gives.** Descending is a negated key or a `reverse`; any number of keys is
  that many passes. Generality reached by composing the smaller thing is
  exactly what **Formatting** settled not to add: *add what cannot be
  composed, refuse what can*.
- **A comparator is a contract the caller can break without being told.** It
  has to be consistent — if `a` sorts before `b` and `b` before `c` then `a`
  must sort before `c` — and nothing checks that, so an inconsistent one does
  not fail. It answers a list that is not in any order, and looks sorted. A
  key function cannot be inconsistent: it hands back one value per element and
  `<` does the rest.
- **It would need two more answers Vine does not want to give**: whether a
  comparator returns a bool or a number, and what a sort does when handed one
  that contradicts itself.

Writing the comparator by mistake is not silent. `sort` calls the key function
with one element, so a two-parameter function is an arity error naming the
function and where it was written — the same error `map` and `filter` give.
See `tests/cases/errors/sort_comparator.vine`.

There is no string shorthand for a field either — `sort(xs, "qty")` is an
error. The key is an expression over the element, which is what lets it be
`-o.qty` or `len(o.item)` and not only a name.

### Why an argument and not a sort written in Vine

`sort(xs)` alone cannot rank records, and the gap is not one a program can
close. Ordering records means carrying each record alongside the value it is
ordered by, *through* the sort, and nothing in Vine can: `sort` refuses a list
of pairs, because a list is not ordered by `<`, and a map keyed on the sort key
drops every record that shares a key.

```
let orders = [{n: "a", q: 3}, {n: "b", q: 1}, {n: "c", q: 3}]
reduce(orders, fn(acc, o) { set(acc, o.q, o) }, {}) |> keys |> len   # 2
```

Three records in, two out, and nothing said about the one that went missing.

The only route left is to stop using `sort` and build an ordering out of `<`.
That is not composing the parts Vine hands you, it is replacing one of them —
the same place `round(x, digits)` stood under **Formatting**. It is also worth
knowing what it costs. Here is a sort by key written in Vine, six lines, and
it is wrong:

```
let insert = fn(sorted, x, key) {
  if len(sorted) == 0 { [x] }
  else if key(x) <= key(first(sorted)) { concat([x], sorted) }
  else { concat([first(sorted)], insert(rest(sorted), x, key)) }
}
let sort_by = fn(xs, key) { reduce(xs, fn(acc, x) { insert(acc, x, key) }, []) }
```

`<=` puts a new element ahead of the one it ties with, so ties come out
backwards. The list is in order, every element is present, and the answer is
not the one stability promises — which is the kind of mistake nobody writes a
test for, because the output looks sorted.

## repr and str

Vine turns a value into text two ways, and what separates them is who reads
it. A number can also be written to a set number of decimal places — see
**Formatting** at the end of this section — which is a third function and
not a third conversion.

`str(x)` is for a person, and `"{x}"` is the same conversion (see **Strings**):
`str("north")` is `north`. `repr(x)` is **Vine source for the value**:
`repr("north")` is `"north"`, quotes and all. Stated exactly —

> for any value `v` holding no function, `repr(v)` is a Vine expression, and
> evaluating it gives a value `==` to `v`.

That is what every escape in `repr` is for, and it is the promise `repr` had
been quietly failing. Before tick 6 the prompt answered this:

```
>>> "\{"
"{"
```

The REPL echoes a value the way `repr` shows it, so it was printing a string
nothing could type: paste it back and Vine says `unterminated string`. Three
values were in that state, all the same shape — no way to write them down:

- `{` in a string, since interpolation made it structural. It is escaped now.
- Floats outside roughly `1e-4` to `1e16`, which print in exponent form.
  Numbers gained an exponent, so they are writable (see **Literals**).
- `inf`, `-inf` and `nan`, which had no source and no prospect of one. So they
  stopped being values instead: a literal too large is a syntax error,
  arithmetic that overflows is a runtime error, and `float("inf")` is refused.
  Vine had already answered `division by zero` rather than `inf`, so this is
  the rule it was half keeping. The cost is that no Vine program can hold a
  float beyond about `1.8e308` even briefly, which is the price of every value
  being writable, and it is small.

**Functions are the exception, and the only one.** A closure is its parameters,
its body *and* the environment it captured; no expression denotes that. One
reprs as `<fn name/arity>`, which is deliberately not parseable, so it cannot
be mistaken for source that would work.

### Inside a container

A container reprs its elements, no matter which conversion was asked of the
container itself:

```
let xs = ["a", "b"]
str(xs)      # ["a", "b"]
"{xs}"       # ["a", "b"]
xs[0]        # a
```

A container's elements come out in the container's own order: a list's, and
for a map the one under **Map order**. Printing is a reading of the value and
does not get to choose an order of its own.

So one call to `str` uses both conversions, at different depths. That reads as
an inconsistency and is not. `str` of a string is its text, because the reader
wants the text. `str` of a list is a description of a list, and a description
with its strings flattened into text could not be read back: the one-element
list holding `a, b` and the two-element list holding `a` and `b` would both
come out `[a, b]`. The rule is that the outermost value is converted
for its reader and everything nested inside it is converted as source — which
is what "how a value looks nested inside another value" had always meant,
without ever saying what it was for.

### Formatting

`str` and `"{x}"` show a number the way Vine writes it down: the shortest text
that reads back as the same value. That is the right answer for a value being
shown on its own and the wrong one for a value in a column. A price is `5.00`
and never `5.0`, and the shortest text for three tenths is
`0.30000000000000004`.

`fixed(x, digits)` is how a number is written to a set number of decimal
places, and it is a builtin rather than syntax:

```
let total = 3 * 0.1
"{total}"                   # "0.30000000000000004"
"{fixed(total, 2)}"         # "0.30"
fixed(5.0, 2)               # "5.00"
total |> fixed(2)           # "0.30"
```

It takes an `int` or a `float` — never a `bool`, which is not a number here —
and a digit count that is an `int` from 0 to 1074, and it returns a string.
`fixed(x, 0)` has no point at all rather than a trailing one. The result is
never in exponent form, so `fixed` is also the way to write a float outside
about `1e-4` to `1e16` out in full.

Three facts a reader meets in this order:

- **Ties go to the even digit.** `fixed(0.125, 2)` is `0.12` and
  `fixed(0.375, 2)` is `0.38`. Rounding halves upwards biases a column of
  totals upwards; this is the rule that does not.
- **The digits are those of the float that is actually there.**
  `fixed(2.675, 2)` is `2.67`, because the float written `2.675` is a hair
  below it. Formatting reports a value, it does not repair one.
- **An int is written from its own digits, never through a float**, so an int
  with more digits than a float can hold keeps every one of them instead of
  rounding at the seventeenth.

The ceiling of 1074 is a fact about floats rather than a number picked for
comfort. The smallest float Vine has is `5e-324`, which is exactly `2^-1074`,
and its decimal expansion ends on a `5` at the 1074th place. So every float
can be written out exactly, and every digit past the ceiling would be a zero.

**Why a builtin and not syntax.** Three other spellings were considered, and
each is refused for a reason worth keeping:

- **Not a hole grammar** — `"{total:0.2}"`. A hole holds exactly one
  expression, and **Strings** gives the reason that rule is worth keeping: a
  hole's expression is lexed in the ordinary token stream, so "any expression"
  is the *absence* of a restriction. A `:spec` suffix would be a second
  grammar to lex, position and report errors in, inside a string, where
  positions are already the hardest thing in the language to get right. It
  would also be the largest borrowed answer Vine has taken: everyone who types
  `{x:.2f}` means another language's, and this would not be it.
- **Not `format(x, "0.2")`.** The same mini-language with the positions taken
  away. A spec that is a runtime string may have been computed, so an error in
  one cannot point at the character that is wrong — and a notation you cannot
  point into is strictly worse than one you can.
- **Not an operator** — `x % "0.2"`. `%` is modulo. Deciding an operator's
  meaning from the type of its right operand, in a language where `1 == 1.0`
  is false, is not a small liberty to take.

Refusing the colon is not free, because every reader arrives already knowing
it, so a hole that reaches for one says what to write instead:

```
syntax error: expected '}' to close the interpolation, found ':'
 --> report.vine:4:14
  |
4 | print("{total:.2f}")
  |              ^
  = help: a hole holds one expression, with no format after it; for decimal places write "{fixed(x, 2)}"
```

A function keeps what none of the three would: `fixed` is a value. It pipes,
it maps over a list, it passes to `reduce`, and a program formatting a column
in two places can bind `let money = fn(x) { fixed(x, 2) }` and use that.

**Why this and not more.** Width, alignment and thousands separators are not
here, and their absence is a decision rather than a deferral. Each of them
turns a string into another string, and each is a line of ordinary Vine over
the string `fixed` has already handed you:

```
let pad = fn(s, w) { join(map(range(w - len(s)), fn(_) { " " }), "") + s }
"east:" + pad(fixed(5.0, 2), 9)          # "east:     5.00"
```

Rounding to a number of digits is the one thing that is not composable: to get
`0.30` out of `0.30000000000000004` you must implement decimal rounding by
hand, in a language whose case for existing is that shaping data should not
ask that. So the rule this settles is **add what cannot be composed, refuse
what can**.

That rule is also why there is no `round(x, digits)`. Rounding is a numeric
operation and what a column wants is textual: `round(5.0, 2)` is `5.0`, and
`str` of it is `"5.0"`, so no amount of rounding ever reaches `"5.00"`. A
rounding builtin was the cheap answer this question was deferred with four
times, and it does not answer it.

**`fixed` is not a third conversion.** `str` and `repr` convert *any* value,
and which applies is decided by who reads the result; that pair stays a pair.
`fixed` takes a number and nothing else, and hands back an ordinary string
that `repr` then quotes like any other. Nothing above changes what `repr(v)`
promises.

## Errors

Every failure in a Vine program is a `syntax error` or a `runtime error`
carrying a position, and is rendered with the offending line and a caret:

```
runtime error: cannot add string and int
 --> example.vine:2:13
  |
2 | print(label + 3)
  |             ^
```

A report may say more than that. Under the caret come any number of extra
lines, each labelled:

```
syntax error: unterminated string
 --> example.vine:1:9
  |
1 | print("{")
  |         ^
  = note: this string is inside the interpolation opened by the '{' at 1:8
  = help: a literal brace is written '\{'
```

A **note** states a fact about this program that the headline leaves out, and
may carry a *second position* — written `line:col`, or `name:line:col` when
it points into a different source than the caret does, which is the ordinary
case in a session:

```
runtime error: greet expects 2 arguments, got 1
 --> <repl:3>:1:6
  |
1 | greet("solo")
  |      ^
  = note: greet is defined at <repl:1>:1:13
```

A **help** offers a rule of the language because it is likely to be the one
wanted. It carries no position, and it is never a claim about what the
program meant.

That split is the contract, not decoration. The caret is where the failure
was *detected*, which is not always where it was caused: a note may name the
cause, and labelling the two differently is what keeps a message from
guessing. `"{"` is the case that forced it — a string really did open at that
quote and never close, so the caret belongs there, and everything the reader
is missing is a fact about a different character.

Messages are written in Vine's words and never the implementation's. The
parser calls a token `ident`; nobody writing Vine has been told what that is.
The standard to meet is `index 5 is out of range for a list of length 3`:
what was asked for, what was there, and nothing to look up first.

A Python traceback reaching the user is always a bug in the implementation.

Running a file exits 0 when the program runs and 1 when it fails, with the
report above on stderr. A problem with the command line itself — an unreadable
file, `-e` with nothing after it, or more than one program named at once —
exits 2 and is reported as `error: ...` with no position, because nothing has
been parsed to have a position in.

One command line runs one program. `vine a.vine b.vine`, and `-e` beside a
file, are refused rather than half-obeyed: running the first and ignoring the
rest exits 0, which reports success for the part that never happened.

## Not in v0.2

Deliberately absent, roughly in the order they look worth adding: early
`return`, a module/import system, a `match` expression, user-defined operators,
and a bytecode compiler. Anything here is fair game for a later tick — but
adding one means adding its tests and updating this file in the same commit.

Audited in tick 7, after three ticks deferred it: all five are absent. `return`
and `import` are not keywords, so `return 1` and `import "x"` are two
statements on one line; `match x { 1 => 2 }` fails at the `=>`, which is not an
operator; there is no syntax that binds one; and `vine/interp.py` walks the
tree. No case guards any of this, deliberately — a test that a feature is
missing passes for as long as nobody is working on it, and fails on the branch
of whoever is, which is the one place the reminder is noise rather than news.
The paragraph above is the reminder, and it is aimed at the right reader.
