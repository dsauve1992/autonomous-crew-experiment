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
./check                         # run the test suite
```

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
Maps preserve insertion order. Anything else offered as a key is an error
wherever a key is expected — in a literal, in `set`, in `get`, in `contains`
and in `m[k]` — rather than a lookup that quietly misses, because a list can
never be a key and asking is a different mistake from asking for one that is
absent. `get(m, k, default)` is for absence.

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
reader can act on. An operator chain does not nest — `1 + 1 + 1` is flat — so
the count is of brackets, blocks, holes and unary operators.

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
  `"{repr(x)}"`.

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
prompt, where the entry is not continued.

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

Numbers: `fixed(x, digits)`

Lists: `range(n)` `range(a, b)` `map(xs, f)` `filter(xs, f)` `reduce(xs, f, init)`
`push(xs, x)` `concat(a, b)` `first(xs)` `rest(xs)` `reverse(xs)` `sort(xs)`
`contains(xs, x)`

Maps: `keys(m)` `values(m)` `get(m, k)` `get(m, k, default)` `set(m, k, v)`

Strings: `split(s, sep)` `join(xs, sep)` `upper(s)` `lower(s)` `trim(s)`
`reverse(s)` `contains(s, sub)`

`push` and `set` return new values; nothing in Vine mutates.

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
file, or `-e` with nothing after it — exits 2 and is reported as `error: ...`
with no position, because nothing has been parsed to have a position in.

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
