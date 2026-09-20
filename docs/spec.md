# The Vine language, v0.2

This is the contract. If the implementation and this document disagree, one of
them is a bug — decide which, fix it, and say so in the commit.

Vine is a small, dynamically typed, expression-oriented language for shaping
data. Everything is an expression; there are no statements except `let`. There
is no mutation and no loop construct: you transform data by passing it through
functions, usually with the pipeline operator.

**How the examples are written.** An untagged code block is Vine, and its
lines are entries at a prompt: a `let` binds for the lines below it. A line
written `expression    # result` claims that the expression answers exactly
that result, and everything after an em dash in the comment is commentary
about it. A result beginning `error:` claims the expression fails with that
message. `tests/properties/spec_examples_run.py` runs every such line on every
`./check`, so a claim made in that shape is checked and a claim made in prose
is not.

## Running it

```sh
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
- Keywords: `let fn if else do return true false nil and or not`.
- Numbers are `123` (int), and `1.5` or `1e-9` (float). See **Literals**.
- Strings are double-quoted and do not span lines. Escapes: `\n \t \r \" \\
  \{ \}` and `\u{...}`. A `{` opens a string interpolation — see Strings.

## Types

`nil`, `bool`, `int`, `float`, `string`, `list`, `map`, `function`.

`int` and `float` are distinct types and are never equal to each other: `1 == 1.0`
is `false`. `type(x)` returns the type name as a string.

A map key may be any value that holds no function, and two keys are the same
key when they are `==` — which is type-strict, so
`{1: "a", 1.0: "b", true: "c"}` has three entries, and structural, so a list
or a map may be one. See **Composite keys**. A map's keys are in an order —
see **Map order** below. A function offered as a key is an error wherever a
key is expected — in a literal, in `set`, in `get`, in `contains` and in
`m[k]` — rather than a lookup that quietly misses, because a function is `==`
to nothing but itself and asking is a different mistake from asking for a key
that is absent. `get(m, k, default)` is for absence.

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

A **value** nested more than 1000 deep is a runtime error as well, reported at
the expression that walked it. Nothing has to recurse to reach it —
`reduce(range(1000), fn(a, i) { [a] }, [])` is a thousand calls that each
return before the next begins, and a value a thousand and one deep — and it
fires the first time anything asks the whole value a question: `==`, `repr`,
`str`, printing it, or offering it as a key. Building it is not the error, and
a program that builds one and never reads it runs.

It is a limit on the **walk** rather than a property stamped on the value:
what is counted is how many containers one question entered. So a map key is
walked from the map when the map is printed, and from itself when it is first
offered as a key, and the same number bounds both. A session's echo of an
entry's value is a walk too — it is `repr` — and it reports like one. It had
not, from the day the prompt existed until the day the limit got a number: a
deep value typed at a prompt ended the session in a Python traceback, because
the echo happens after the entry has finished running and nothing was
watching it there.

**Why there is a number at all**, since for thirty-two ticks there was not
one. The walk belongs to the implementation and the limit used to be its
stack, which made *whether a program works* a fact about the machine and about
the rest of the program rather than about the value. Measured on one machine
in one process: `x == x` stopped at 3489 at the top level and at 1995 inside
498 calls, and `print(x)` stopped at 2329. Two programs holding the same value
disagreed about whether it was a program.

The premise that this belonged to the machine was wrong, and one line of the
implementation held it up. `print` built its output by handing a generator to
Python's `join`, which calls back into Python from C — so every container the
walk entered cost a slot of the C stack, the one stack no setting can grow. On
a 512KB stack that walk stopped at depth 232, on 1MB at 474, on 8MB at 3873.
`==` and the key identity, which recurse through ordinary frames only, reached
60000 on all three. Build the parts into a list and hand *that* to `join`, and
it calls nothing; every walk in the language is then as portable as the other
two limits already were, which the same measurement confirms — a 500-deep call
chain and a 200-deep literal both report Vine's limit on a 512KB stack.

**Why 1000.** Not the corpus, which is the measure **Expressions** uses and is
no use here: every hand-written value in this repository is **two** deep, and
the only deeper ones are the two cases that test this limit. A value gets deep
in a loop, and nobody writes that loop for the look of it. The constraints are
the other two limits. A literal at the parser's ceiling is 200 deep, so a
number below that would let the parser accept a program that builds a value
nothing can print. And a value that gains a level per *call* — which is the
shape of every recursive builder — meets the call limit at 500 first, and
`call depth exceeded 500 (infinite recursion?)` is the better message for it.
So what reaches 1000 is a value built by a loop, which is what this limit is
for.

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
repository nests **twelve** levels — `examples/timesheet.vine`, at a line that
prints one row of a table — and a map literal ten containers deep is eleven.
The limit is about seventeen times what hand-written Vine has ever asked for,
which is the check the number had been missing rather than a reason to move
it.

Seven was the answer until tick 27, when the first program longer than forty
lines was written and went to twelve without reaching for anything unusual:
a call inside a call inside a list inside a call inside a function body is
how a report prints a row. The number is a measurement of the corpus and
moves when the corpus does; what it is here to say is the ratio.

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

Five decisions, and the reasons, because syntax is the part that cannot be
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
- **A codepoint is written `\u{...}`.** Hex digits in braces, either case, and
  it is the escape for everything the other seven do not reach. What it is for
  is the characters a reader cannot see: `\u{1e}` is a record separator and
  `\u{a0}` a non-breaking space, and `trim` removes both — see **Text**.
  Before it they reached a string only by being pasted into a literal, which
  worked and left a line of source nobody can read, and a *file* whose subject
  is a character that every rendering of it drops. There is one limit and not
  two: the digits are not counted, so `\u{41}` and `\u{000041}` are both `A`,
  and what is checked is the value. Past `\u{10ffff}` is a syntax error, and so
  is a surrogate half — `\u{d800}` through `\u{dfff}` — not on taste but
  because a string holding one cannot be printed at all, and printable is what
  every Vine value is. An escape makes a *character* and never syntax, so
  `\u{7b}` is a brace that opens no hole and `\u{22}` a quote that ends no
  string.
- **The value is converted the way `str` converts it, not `repr`.**
  `"hi, {name}"` must produce `hi, vine`, not `hi, "vine"`; quoting every
  string hole would need undoing at almost every use. So `"{x}"` and `str(x)`
  can never disagree, and the other conversion stays one call away as
  `"{repr(x)}"`. That is a rule about the value the hole holds and not about
  what is inside it: a list in a hole still shows its elements as source, so
  `"{["a", "b"]}"` is `["a", "b"]` with the quotes. The hole inherits that
  from `str` along with everything else — see **Inside a container**, which
  says why the two depths differ.

```
"\u{48}\u{49}"                # "HI"
"\u{41}" == "\u{000041}"      # true
len("\u{1f600}")              # 1
len("\u{7b}1 + 1\u{7d}")      # 7 — a brace that opens no hole
"\u{d800}"    # error: codepoint escape '\u{d800}' is a surrogate half, not a character
```

A hole is an ordinary piece of the program, so a failure inside one is an
ordinary error, pointing into the string at the part that failed:

```
let label = "x"
print("value: {label + 1}")
```

```report
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
really did begin, and both carry a note naming the `{` that was still open
when the line ended. The `#` case carries a second note naming the `#` as
well, because the closing quote the comment swallowed is still on the screen
for the reader to point at.

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
`nil` if it is empty or ends in a `let`. A function may also leave early — see
**Early return**.

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

## Early return

```
return expr
return
```

`return` leaves the enclosing function with that value; a bare `return`
answers `nil`, which is what a function ending in a `let` already answers.
Statements after it do not run.

**It is a statement, not an expression.** `let x = return 1` and `f(return 1)`
are syntax errors, and so is `1 + return 2`. A `return` has no value to give
the expression around it — it abandons that expression — and a grammar that
says so costs one rule, where an expression that never yields costs every
reader a special case to remember. What the refusal reads as is the message
any keyword in that position gets:

```
let x = return 1
```

```report
syntax error: expected an expression, found the keyword 'return'
 --> report.vine:1:9
  |
1 | let x = return 1
  |         ^
```

**It is refused outside a function, and refused at parse time.** Whether a
`return` has a function to leave is a property of where it is written, not of
what happens when the program runs, so the parser is where it is answered and
a `return` at the top of a file never runs at all:

```
return 1
```

```report
syntax error: 'return' outside a function
 --> report.vine:1:1
  |
1 | return 1
  | ^
  = help: only a function body may return; a block's value is its last statement
```

That refusal is also what makes the feature safe to implement the way it is:
`return` is a signal thrown out to the call that will answer with it, and
because no `return` can exist without a call beneath it, no signal can reach
a reader as anything but a value.

**A block is not a function.** `do { return x }` inside a function leaves the
*function*, not the block — the same for a branch of an `if`, which is also a
block. There is nothing a `return` can leave but a function, so there is
nothing to be ambiguous about, and `return` inside a `do` at the top level is
the refusal above.

### Why `return` earns its keyword

`if` is an expression and `else if` chains, so most guards in Vine are already
flat and `return` buys them nothing. Where it pays is a guard whose binding is
only *valid* once the guard above it has passed. Hoisting the bindings above
the chain is the flattening that needs no new syntax, and it works right up
until it does not:

```
let head_price = fn(orders) {
  let first = orders[0]
  if len(orders) == 0 { 0.0 }
  else if type(get(first, "unit", nil)) != "float" { 0.0 }
  else if first.unit < 0.0 { 0.0 }
  else { first.qty * first.unit }
}
head_price([])
```

```report
runtime error: index 0 is out of range for a list of length 0
 --> report.vine:2:21
  |
2 |   let first = orders[0]
  |                     ^
  = note: head_price was called at 8:11
```

The empty list is the one input the length check exists to survive, so that
binding cannot be hoisted, and without `return` those three guards are a
three-deep nest ending in a branch four levels in. With it they are three
lines down the left margin:

```
let head_price = fn(orders) {
  if len(orders) == 0 { return 0.0 }
  let first = orders[0]
  if type(get(first, "unit", nil)) != "float" { return 0.0 }
  if first.unit < 0.0 { return 0.0 }
  first.qty * first.unit
}
```

Both programs are in `tests/cases/return.vine`, which is also where the
hoisted one is not, because it does not run.

### What it costs

`return` is a keyword, so it is no longer a name. `let return = 1`,
`fn(return) {...}`, `o.return` and the bare-identifier map key `{return: 1}`
are all syntax errors now, each naming the keyword it found. A map key of that
spelling is still reachable as a string, which is the escape hatch every other
keyword already has and the first tick to need it:

```
{"return": 1}                      # {"return": 1}
let o = {"return": 1}
o["return"]                        # 1
```

**A statement after a `return` is not refused.** It is dead, and Vine says
nothing. The parser could see the trivial case and could not see
`if c { return 1 } else { return 2 }` followed by a statement, which is dead
for the same reason and needs flow analysis to know it. Half a rule about
unreachable code would be worse than none: a reader who learned that Vine
catches this would be wrong most of the time they relied on it.

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

General: `type(x)` `len(x)` `str(x)` `int(x)` `int(s, default)` `float(x)`
`float(s, default)`

Numbers: `fixed(x, digits)` `pow(x, y)`

Lists: `range(n)` `range(a, b)` `map(xs, f)` `filter(xs, f)` `reduce(xs, f, init)`
`push(xs, x)` `concat(a, b)` `first(xs)` `rest(xs)` `take(xs, n)` `drop(xs, n)`
`reverse(xs)` `sort(xs)` `sort(xs, key)` `contains(xs, x)`

Maps: `keys(m)` `values(m)` `get(m, k)` `get(m, k, default)` `set(m, k, v)`

Strings: `split(s, sep)` `join(xs, sep)` `upper(s)` `lower(s)` `trim(s)`
`reverse(s)` `contains(s, sub)` `reveal(s)`

`push` and `set` return new values; nothing in Vine mutates.

Nearly every name above has a section of its own — **Printing**,
**Conversions**, **Text**, **Looking up a key**, **Range**, **Powers**,
**map, filter and reduce**, **Building lists**, **Taking and dropping**,
**Sorting**, **repr and str**, **Revealing**, **Formatting**. A builtin whose
whole contract
is its line of this roster has not been decided; it has been implemented, and
the first program that asks it a question the roster does not answer will get
whatever the implementation happens to do.

None are still in that state. The last two, `len(x)` and `reverse(x)`, are
**len and reverse**, which was written by asking them what they mean for every
type they accept and why they refuse the rest. `type(x)` has no section either
and does not need one; **Types** lists the eight names it can answer, which is
the whole of it.

## Printing

`print(...)` writes to standard output and answers `nil`. It is the only
builtin that does anything other than compute a value, and the one builtin no
composition can replace: no other expression in Vine writes. Everything
*around* the writing does compose, and that is the rest of this section.

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
ordered pair of the value list in `tests/properties/no_traceback.py` by
`tests/properties/composition_holds.py`, with no disagreement. So the space is
a convenience and nothing else, and a reader who wants another separator
writes the composition out:

```
print(join(["north", "south"], ", "))      # north, south
print(join(map([1, 2.5], str), ""))        # 12.5
```

It is a space rather than a comma because a comma is a **format**, and
**Formatting** keeps formats out of the thing that shows a value: a separator
between two columns is the same kind of decision as a decimal place, and
`fixed` is where that decision is made. One space is the only choice that is
not a format — it is the least that separating two things at all can cost.

**It shows a value the way `str` does, not the way `repr` does.**
`print("a")` writes `a` with no quotes and `print(["a"])` writes `["a"]` with
them. That is **Inside a container** rather than a rule of its own: at the top
level you are being shown a value, and inside a container you are being shown
structure.

**`print` never fails.** `str` converts every value and never fails — see
**Conversions** — so there is no value `print` refuses. That is a consequence
rather than a measurement: nothing enumerates it, and
`tests/cases/printing.vine` prints one value of every type. It is what makes
`print` the call you can drop into the middle of a program to see what is
flowing through it, and it is why **map, filter and reduce** and **Sorting**
promise *when* a function runs: a function handed to `map` may print, and a
promise about printing is worth nothing if printing can fail.

**It answers `nil`, so it does not pass its argument through.** `xs |> print`
is `nil` and not `xs`. A pipeline that wants to look at what it is carrying
names the value:

```
let tap = fn(xs) {
  print(xs)
  xs
}
tap([1, 2]) |> take(1)      # [1] — after printing [1, 2]
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

**An int is as wide in text as it is in arithmetic.** **Powers** says ints are
unbounded; reading and writing one is the same number said another way, so
`int(s)` reads a string of any length, `str(n)` writes one, and
`int(str(n)) == n` at every width. Until tick 28 that held only to 4300
digits, which is the point at which the implementation refused and took the
program with it — and the width is reached by multiplying, not only by typing
a long literal, so the program that met it first had no long number in it.
What is bounded is the time: writing out an enormous int is quadratic, which
is the slow program **Powers** already describes and not a failure.

A string that is not a number by anyone's reading is refused with the headline
alone: `cannot convert "abc" to an int`. One that Vine refuses and something
else would read carries the rule as a help, because every character of
`"1_000"` was meant as part of a number and the headline on its own reads like
a mistake.

That second kind also carries the value **written out in escapes**, when
writing it out shows anything the quoted text did not:

```
let row = "١٢٣"
print(int(row))
```

```report
runtime error: cannot convert "١٢٣" to an int
 --> report.vine:2:10
  |
2 | print(int(row))
  |          ^
  = note: written out in escapes, that string is "\u{661}\u{662}\u{663}"
  = help: the digits are 0 to 9, optionally signed, with spaces, tabs or newlines around them
```

Those are digits, and they are not the digits `int` reads. Without the note
the headline quotes the value back and *looks right*, which is the one way a
true message can leave a reader with nowhere to go. `int("café")` gets
neither line: it is refused before that branch, and a reader who can already
see the value has nothing to gain from `"caf\u{e9}"`. `int("1_000")` gets the
help and not the note, because writing it out shows the same five characters.

### When the text is not a number

`int(s, default)` and `float(s, default)` answer the default instead of
failing:

```
let field = "n/a"
int(field)                 # error: cannot convert "n/a" to an int
int(field, nil)            # nil
float("2.5", nil)          # 2.5
float("1e400", nil)        # nil — the shape of a number, and no float
float([1], 0)              # error: cannot convert a list to a float
```

**Why a default and not a predicate.** The two-argument form is the
one-argument form with its failure answered, so there is one reading of the
grammar in the implementation and there can only ever be one. The obvious
alternative — `is_number(s)` and `is_int(s)` as builtins — puts the grammar in
two places and asks somebody to keep them equal. That is not a hypothetical
cost: `examples/timesheet.vine` had to write the predicate by hand, and the
hand-written one and `float` had *already* disagreed about `"1e5"`, which
`float` reads as `100000.0` and the copy called not a number. Section 1 of
`docs/writing-a-program.md` is the measurement, and this feature is its
answer.

The predicate is not lost, because it composes:

```
let is_number = fn(s) { float(s, nil) != nil }
["1", "x", "1e5", "1.", "1_0"] |> filter(is_number)    # ["1", "1e5", "1."]
```

which pipes and maps like any other function, and is the same reading of the
grammar rather than a second one. `tests/properties/conversion_default.py`
enumerates that equality — `float(s, nil) != nil` is exactly *`float(s)`
answers* — over every string of three characters or fewer built from the
thirteen characters that decide the question, because a composition a refusal
rests on is owed its domain and not an example.

**What a default covers.** Text that is not a number, and nothing else. Every
failure of the one-argument form over a *string* becomes the default —
`"abc"`, `""`, `"١٢٣"`, `"1_000"`, `"2.5"` asked of `int`, and `"1e400"` asked
of `float`, which has the shape of a number and is past every float there is.

Every other failure stays a failure, with or without a default:

```
let huge = reduce(range(100), fn(a, i) { a * 10000000 }, 1)
float([1], 0)              # error: cannot convert a list to a float
int(nil, 0)                # error: cannot convert nil to an int
float(huge, 0.0)           # error: int is too large to convert to a float
```

This is the line **Looking up a key** already draws for `get`: a list offered
where a map belongs is a mistake worth naming rather than a lookup that
missed, and a list offered where text belongs is the same mistake. A default
says *this data may be wrong*; it does not say *this program may be wrong*. A
conversion that hid a category error behind a default would hide it forever,
because the value a list converts to is a value the program then goes on to
use.

A call that passes a default and fails anyway carries the rule as a help,
because that reader has asked for exactly the question it answers:

```
let row = [1]
print(float(row, 0.0))
```

```report
runtime error: cannot convert a list to a float
 --> report.vine:2:12
  |
2 | print(float(row, 0.0))
  |            ^
  = help: a default answers for text that is not a number, and for nothing else
```

**A default never changes an answer that exists.** `int("17", 0)` is `17`,
`int(2.9, 0)` is `2`, `int(true, 0)` is `1`. The second argument is reached
only where the first form raises, which is what makes adding one to a working
call a no-op rather than a hazard.

**The default is a value, of any type, and it is always evaluated.** It is an
ordinary argument, like `get`'s: `float(s, nil)` answers `nil`, which is not a
float, and that is the caller's choice and not a promise `float` broke. The
type a conversion returns is `int` or `float` *or whatever you said*.

**Prefer `nil`.** A plausible default is worse than no default at all. The
program this feature was written for exists to name the line that was wrong,
and `float(field, 0.0)` would have logged zero hours and said nothing —
a number that is wrong is indistinguishable from a number that is right, while
`nil` is the one default that can be tested:

```
let hours = float(f[3], nil)
if hours == nil { return complaint(n, "hours is not a number") }
```

Those two lines replace eleven of hand-written grammar. The cost is real and
worth stating: a default discards the report, and the report was good. `int("١٢٣")`
explains that those are digits and not the digits `int` reads, and
`int("١٢٣", nil)` says nothing at all. A program that converts with a default
takes on the job of complaining, and that is the trade — which is why both
forms exist, and why the one that fails is still the one to reach for when the
data is supposed to be right.

**What was refused: a catchable failure.** The general answer — an error a
program can catch, or a conversion that returns a result value carrying
success beside the number — was considered and is not here. It changes what an
error *is* in this language, everywhere, to solve a problem two arguments
solve; nothing in `examples/timesheet.vine` wanted it; and it would leave
`get`'s four spellings and this one saying different things about the same
question. If it is argued again, the argument is not conversions. See **Not in
v0.2**.

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
Unicode calls whitespace — twenty-nine of them today, including the
non-breaking space and the four ASCII information separators — where the lexer,
`int` and `float` all take the same four. The two sets differ because they read
different things: source never contains a non-breaking space and scraped data
is full of them, and `trim` is what a report calls on a column before anything
else. The cost is that `trim` takes a record separator off data delimited by
one, and the answer is to trim the fields rather than the record:

```
let row = " a b "
len(split(row, " "))                  # 4 — two values and the two ends
len(split(trim(row), " "))            # 2 — trim ate the outer delimiters
map(split(row, " "), trim)            # ["", "a", "b", ""] — still 4
```

That holds for any separator, including the ones `trim` eats. Those have no
glyph, so they are written as codepoint escapes — `\u{1e}` for a record
separator, `\u{a0}` for a non-breaking space, see **Strings** — and a program
that splits on one says so in a line a reader can read:

```
len(split("a\u{1e}b", "\u{1e}"))      # 2
```

**`trim` is the one builtin whose answer moves.** *Today* is load-bearing in
that count: which characters Unicode calls whitespace is a property of a
Unicode release, and Vine asks the host's table. **repr and str** refuses a
moving table on exactly this ground three sections down, and the two are not
in conflict — they are answering for two different readers. `repr(s)` is a
*value*: a program compares it, prints it and writes it to a file, so an
answer that differs between two machines is a bug in the program that stored
it. `trim(s)` is the first thing a report does to a scraped column, where the
question is what a person would call blank, and the standard's current answer
to that is better than a frozen one. `tests/properties/whitespace_is_two_sets.py`
pins both sets, so the day the table moves under the document, `./check` says
so rather than the document quietly going stale.

Until tick 20 there was no such escape and they reached a string only by being
pasted into a literal. That worked — the lexer took the character, `len`
counted it and `repr` handed it back — and it left every line holding one
illegible, in exactly the place where what the line says is which character it
means. See **repr and str** for the half of that which was `repr`'s.

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
In a map it looks for a *key*, so a needle no key could be — a function, or
anything holding one — is an error rather than `false`: that is a category
mistake and not a lookup that missed. A list and a map are keys (see
**Composite keys**), so those are fair questions with real answers. Absence is
what `get(m, k, default)` is for.

**The three also have three prices, and the gap is the widest in the
language.** A string is searched, a list is scanned element by element with
`==`, and a map is one hash lookup. Asking twenty thousand questions of five
thousand names is **19.80s** when the names are a list and **0.20s** when they
are a map — a hundred to one, for one character of difference at the call and
none at all in the answer. Which container a program keeps its names in is
usually decided by what else it does with them; when membership is the
question being asked in a loop, it is decided by this. See **What the fold
costs** under **Building lists**, which is the same choice arriving from the
other side.

### Why there is no `replace`

`replace(s, from, to)` is `join(split(s, from), to)`, and the rule is **add
what cannot be composed, refuse what can**. A refusal on that ground is a
measurement, so here is the measurement.

Over every string of up to four characters drawn from `a`, `b` and a record
separator, paired with every `from` and `to` drawn from seven strings — 5929
triples — and over 200000 more drawn at random from a pool holding a combining
acute, a non-breaking space and an astral codepoint, the composition and a
left-to-right replace disagree on **nothing** with a non-empty `from`. Not
almost nothing, as `pow(x, 0.5)` and a square root turned out to be under
**Powers**: nothing.

They disagree on 726 of the grid's triples, and every one of those has an empty
`from`. `join(split("abc", ""), "-")` is `"a-b-c"`; a `replace` copied from
another language answers `"-a-b-c-"`, putting the replacement where no needle
was found, and on `""` answers `"-"` where the composition answers `""`. Both
readings are defensible and the question is one no program asks, so refusing
the builtin refuses the question with it — which is the cheaper outcome, since
**`split` and `join` are a pair** already settled why `split(s, "")` is the
codepoints and `split("", "")` is `[]`, and a `replace` would have had to
disagree with one of those or with every other language.

**What the refusal costs.** The composition written wrong mostly answers
instead of failing:

```
join(split("a,b", ","), ";")     # "a;b" — right
join(split("a,b", ";"), ",")     # "a,b" — the two strings swapped: the input back
join(split(",", "a,b"), ";")     # "," — subject and needle swapped: the needle
split(join("a,b", ","), ";")     # error: join target must be a list, got string
```

Two of the three ways to get it wrong produce a plausible value, and by **A
composition has two costs** that is exactly where a name earns its place: it
buys a spelling that cannot be got wrong. `replace` does not buy one.
`replace(s, to, from)` is the same mistake with the two strings adjacent, the
same type and one comma apart, which is where argument swaps come from in the
first place; `join(split(...))` at least puts each string next to its own verb.
`push` went in because it has no brackets to drop. `replace` moves this mistake
rather than removing it, so the second cost does not pay for it either.

What a program that wants the narrow set should reach for is above: trim the
fields, not the record.

## len and reverse

Both take one argument, and both are about the shape of a value rather than
what is in it, so what they accept is most of what they mean.

`len(x)` is how many things `x` holds: codepoints in a string (**Text**),
elements in a list, entries in a map (**Looking up a key**).

`reverse(x)` hands back a list or a string with the same things in the
opposite order. It goes one level deep — the elements are not themselves
reversed — and it is its own inverse:

```
reverse([[1, 2], [3, 4]])          # [[3, 4], [1, 2]]
reverse(reverse([1, 2])) == [1, 2]  # true — and so for every list and string
reverse([])                        # [] — and reverse("") is ""
```

On a string that is codepoints, which **Text** settles once for everything
that walks one, including the consequence: a combining accent comes back on
whatever letter now precedes it.

**Both refuse every other type, and `nil` is the one worth a reason.**
`len(nil)` would have to be `0` — there is no other candidate — and `0` is the
wrong thing to hand back, because **Taking and dropping** makes `nil` what an
empty list answers. `len(first(rows))` on an empty `rows` is a program that
has already lost the value it is counting, and `0` is an answer it can carry
on from. The error stops it and names the type. Bools, numbers and functions
hold nothing under any reading and are refused for the ordinary reason.

**`reverse` refuses a map, although a map has an order.** By **Map order** the
call means something: the keys are in the order they first appeared. By the
same section `==` does not compare that order, so the map it answered would be
`==` to the map it was handed:

```
let m = {a: 1, b: 2}
let r = reduce(reverse(keys(m)), fn(acc, k) { set(acc, k, get(m, k)) }, {})
m == r                             # true
keys(m) == keys(r)                 # false
repr(r)                            # {"b": 2, "a": 1}
```

A builtin whose result is always `==` to its argument is not a transformation.
The only thing it could change is how the map prints, and **Map order**
declines to make `repr` canonical for the reason it declines to sort: the
order is the one thing somebody wrote. What a program wants when it reaches
for this is an order to walk in, and an order is a list — `reverse(keys(m))`
is `["b", "a"]`. The three lines above are what putting one back into a map
costs, and that price is the point: it is paid by the program that really did
want the map re-ordered, and not by `==`.

## Looking up a key

Four spellings ask a map about a key. They agree on every key the map has, and
the whole of their difference is what they do when it does not have it — which
is worth four spellings, because a key that is not there is four different
situations.

```
let m = {name: "vine", version: 1}
m.name                 # "vine"
m["version"]           # 1
get(m, "kind")         # nil
get(m, "kind", "?")    # "?"
contains(m, "kind")    # false
m["kind"]              # error: a map of 2 keys has no key "kind"
```

- **`m.k` and `m["k"]` fail.** `{a: 1}["z"]` is
  `runtime error: a map of 1 key has no key "z"`. This is the spelling for a
  key the program requires — a field of a record it is reading — where a missing one
  means the data is not what the program was written for, and stopping at the
  lookup names the key instead of letting a `nil` travel.
- **`get(m, k)` answers `nil`.** The spelling for a key that may or may not be
  there, where absence is not an event.
- **`get(m, k, default)` answers the default.** The same question with the
  caller supplying the absent case, which is what makes accumulating a map
  short: `set(m, k, get(m, k, 0) + 1)` counts.
- **`contains(m, k)` answers whether it is there**, and nothing about the
  value. It is the only one of the four that asks the actual question, and the
  only one that can tell a key holding `nil` from no key.

**The failing one names the map's size, and not its keys.** `map has no key
"z"` said what was asked for and nothing about what was there, which is half
of the standard **Errors** sets for itself. The fact it now adds is a count,
for the same reason `index 5 is out of range for a list of length 3` names a
length and never the elements: a message summarises the container it failed
in. A list's summary happens to be complete — a length says exactly which
indexes are valid — and a map's is not, so the count is the weaker fact and
is still the only bounded one. Listing some of the keys would be worse than
listing none, because a reader shown five of two hundred reads the five as
all of them; listing all of them has no bound. What the count does answer is
`an empty map has no key "north"`, which is a different bug from a missing
key and used to read the same.

**`get(m, k)` cannot tell a missing key from a key holding `nil`.** Both
answer `nil`. That is the same ambiguity `first([])` has — **Taking and
dropping** names this function as the thing that removes it for maps — and
here the removal is real, because the default is reached only when the key is
*absent* and never because the value is falsy:

```
let m = {a: nil}
get(m, "a", 0)     # nil — the key is there, and holds nil
get(m, "z", 0)     # 0 — the key is not there
contains(m, "a")   # true
```

Worth reading twice, because every language that has this function has an
opinion about it and they are not all this one. A default here is not a
replacement for a falsy value: `get(m, k, 0)` on a key holding `nil` answers
`nil`, and on a key holding `false` answers `false`. **Truthiness** is not
consulted at all.

**Why the two-argument form answers `nil` rather than failing.** Because
`m[k]` is already the spelling that fails, and a language with only that one
has no way to tolerate a missing key at all. The two forms of `get` are then
the two ways of tolerating it, and the split between them is not *is this an
error* but *who says what absent looks like*. It is the mirror of `first`,
decided the other way for the reason **Taking and dropping** gives: a list has
no first element only when it is empty, which is `len(xs) == 0` and is usually
the question that was meant, while a map key came from somewhere else and
missing is ordinary.

`get`'s target is a map and nothing else — `get([1], 0)` is an error and not
an index, because a list is indexed with `xs[0]` and a list offered where a map
belongs is a mistake worth naming. What may be a key is in **Types**, and it is
the same rule in `get`, `set`, `contains`, `m[k]` and a literal.

**`keys(m)` and `values(m)` are the whole map.** They are lists of the same
length in the same order — see **Map order** — so a map taken apart by them
goes back together:

```
let ks = keys(m)
let vs = values(m)
reduce(range(len(ks)), fn(acc, i) { set(acc, ks[i], vs[i]) }, {})
```

which is `==` to `m` and in `m`'s own key order. `keys({})` and `values({})`
are both `[]`, and `len(m)` is `len(keys(m))`. Neither builtin takes anything
but a map; for the values of a list there is nothing to ask.

### Composite keys

A key may be **any value that holds no function**: `["mary", "2026-01-05"]` is
a key, so is `{who: "mary", day: 5}`, so is `nil`. `print` is not, and neither
is `[print]`.

The line is drawn by `==` rather than by a list of types, because `==` is what
decides whether two keys are one key, and `equal` already answers that
question structurally for every value there is — except a function, which it
answers by identity. Two closures written the same way are not `==`, so a key
holding one could be found again only by a program still holding that exact
closure, and every other lookup would miss. A key that can only miss is the
thing this section exists to remove, so it is the one thing refused:

```
set({}, print, 1)        # error: a map key may not be a function
set({}, [print], 1)      # error: a map key may not hold a function, got list
```

Both reports offer the rule; the second also says *where*, on a note reading
`the function is at [0] inside the key`. A key is one expression and the part
of it that is wrong may be several fields down a record assembled somewhere
else, which a caret cannot point at and a note can.

**What makes this safe is that Vine has no way to change a value.** `set`,
`push` and `concat` all answer new values — see `tests/cases/immutability.vine`
— so a list handed to `set` as a key cannot afterwards become a different
list. Composite keys are absent from most languages because there they would
be a hazard; here there is nothing to guard.

**What it replaces, measured.** A total per person per day has a pair for a
key. Three spellings, one program, all three run:

```
let rows = [
  {who: "mary jane", date: "2026-01-05", hours: 13.0},
  {who: "ada", date: "2026-01-05", hours: 4.0},
  {who: "mary jane", date: "2026-01-06", hours: 13.0}
]

let flat = reduce(rows, fn(m, r) {
  set(m, "{r.who} {r.date}", get(m, "{r.who} {r.date}", 0.0) + r.hours)
}, {})
map(keys(flat), fn(k) {
  let p = split(k, " ")
  "{p[0]} on {p[1]}"
})      # ["mary on jane", "ada on 2026-01-05", "mary on jane"]

let nested = reduce(rows, fn(m, r) {
  let row = get(m, r.who, {})
  set(m, r.who, set(row, r.date, get(row, r.date, 0.0) + r.hours))
}, {})
reduce(keys(nested), fn(out, who) {
  concat(out, map(keys(nested[who]), fn(d) { "{who} on {d}" }))
}, [])  # ["mary jane on 2026-01-05", "mary jane on 2026-01-06", "ada on 2026-01-05"]

let pairs = reduce(rows, fn(m, r) {
  set(m, [r.who, r.date], get(m, [r.who, r.date], 0.0) + r.hours)
}, {})
map(keys(pairs), fn(k) {
  "{k[0]} on {k[1]}"
})      # ["mary jane on 2026-01-05", "ada on 2026-01-05", "mary jane on 2026-01-06"]
```

**The first is wrong and the run exits 0.** *mary jane* has become a person
called *mary* on a day called *jane*, and her two different days now read as
one line printed twice. The separator is not the bug — no separator works,
because the program cannot check that the data does not contain it, and a
name is data. This is the answer that looks least broken and is least
correct.

**The second was always available and always correct.** A map of maps needs
no separator and tells no lie. What it costs is in its output: `ada` has moved
to the end. `keys(nested)` is people in the order they first appeared and
`keys(nested[who])` is that person's days, so the reading is by person and
then by day, and the order in which the *pairs* first appeared is gone — it
was never stored. The second cost is the `reduce` with a `concat` in it:
every question about all the pairs has to descend two levels to reach them,
so a filter over pairs is four lines where the flat one is one. Neither cost
shows up in a type, and `examples/timesheet.vine` used this spelling for one
of its two tables and the string for the other.

**The third is the pair, kept as a pair.** It is the first spelling's length
with the second spelling's truth, and `k[0]` and `k[1]` are the parts back
without a `split` that can be wrong.

**Equality is `==`, at every depth.**

```
set({}, [1], "int")[[1.0]]                      # error: a map of 1 key has no key [1.0]
{{a: 1, b: 2}: "x"} == {{b: 2, a: 1}: "x"}      # true
```

`[1]` and `[1.0]` are two keys for the reason `1` and `1.0` are: `==` is
type-strict one level down as well. `{a: 1, b: 2}` and `{b: 2, a: 1}` are one
key, because **Map order** says `==` does not compare a map's order — so a map
used as a key has an order for printing and none for identity, which is what
it already had as a value.

**Which spelling comes back out.** When two `==` keys are spelled differently,
`keys(m)` hands back the one that arrived first. That is **Map order**'s rule
for a key's *place*, one level down, and for the same reason: an update is not
a rewrite of what the data first said.

```
let m = set({}, {a: 1, b: 2}, "first")
set(m, {b: 2, a: 1}, "second")      # {{"a": 1, "b": 2}: "second"}
```

**`repr` is still source.** The promise in **repr and str** holds over keys of
every shape, which is checked by `tests/properties/repr_is_source.py`:

```
repr({["a", "b"]: 1, nil: 2})       # {["a", "b"]: 1, nil: 2}
```

**Two mistakes the syntax now makes possible.** A bare identifier in a map
literal is still shorthand for its own name as a string, and inside brackets
it is not:

```
{a: 1}        # {"a": 1}
let a = 9
{[a]: 1}      # {[9]: 1}
```

So `{[who]: 1}` is a key built from the variable `who`, and `{who: 1}` is the
key `"who"`; the two look alike and are two different programs. The shorthand
is not extended into a list, because a list literal is an expression
everywhere else in the language and one place where its elements meant
something different would be worse than the resemblance. Second, a two-part
key is indexed with two brackets:

```
let m = {["a", "b"]: 1}
m["a", "b"]   # error: expected ']', found ','
m[["a", "b"]] # 1
```

**`nil` became a key, and that has a price worth naming.** It was refused
before, and the refusal was catching something: a field read with `get` and
used as a key. That catch is gone.

```
let rec = {name: "x"}
set({}, get(rec, "who"), 1)   # {nil: 1}
```

The spelling that still catches it is the one that was always the right one
for a field the program requires, and it names the field rather than the key
rule:

```
let rec = {name: "x"}
set({}, rec.who, 1)           # error: a map of 1 key has no key "who"
```

`get(rec, "who")` is the spelling that *asked* for absence to be tolerated —
see **Looking up a key** — so a program that writes it and is then surprised
by a `nil` key has been answered by the function it called. `nil` is a key
because the rule is `==` and `nil == nil`; carving it out would also have to
carve out `[nil]`, and a list with a hole in it is exactly the data a
composite key is for.

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

That message has a second half which is the machine's, and it is the one
place left in the language where a limit is. A count that fits the machine's
word and not its memory raises the same message, and there the size that
fails is whatever the process had. **Bindings** has just removed a limit of
that shape by counting it, and this one does not go the same way, which is
worth saying rather than leaving as an omission. Value depth only looked like
the machine's: the implementation had spent a resource it did not need to,
and once it stopped, a thousand was a thousand everywhere. A list of a hundred
billion elements needs eight hundred gigabytes on every machine there is. No
implementation change makes that portable, and a *number* — a longest list —
would be a new rule of the language rather than the writing-down of one, and
would refuse programs that work. So it stays the machine's, and the
difference is that this is now a decision with a reason under it.

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
pow(10, 3) == 1000          # false — because 1000.0 is not 1000
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
print(2 ** 3)
```

```report
syntax error: expected an expression, found '*'
 --> report.vine:1:10
  |
1 | print(2 ** 3)
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

137 of the first 100000 whole numbers land on the wrong side. That count is a
measurement of the host's `pow` against a correctly rounded root, taken once
and deliberately guarded by no test: it is a fact about the floating-point
library Vine is running on rather than about Vine, so a test would assert
something a Python upgrade may change for reasons this language has no opinion
about. Read it as an order of magnitude that was checked, not as an invariant.
So `sqrt` is not *strictly* composable, and it is refused anyway: one ulp is nine
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
Over the value list of `tests/properties/no_traceback.py` the two agree on
every pair of lists and on no other pair whatever, because `+` also adds two
numbers and joins two strings while `concat` refuses both and names the side
that was not a list. `tests/properties/composition_holds.py` checks both of
those directions, because where they agree is the claim and not that they
agree. So `concat` is one third of `+` with the other two thirds taken away,
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
invisible when they are wrong.** Over every list in that value list paired
with every value in it the two never disagree, so this one composes exactly,
and the rule as written refuses it. The exception is not about what the
composition answers; it is about what the composition costs to write. It has
a one-element list literal in it, and dropping those brackets is not an error:

```
let rows = [["north", 1]]
let row = ["south", 2]
concat(rows, [row])    # [["north", 1], ["south", 2]] — two rows
concat(rows, row)      # [["north", 1], "south", 2] — a row and two strings
push(rows, row)        # [["north", 1], ["south", 2]] — two rows
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
`concat right argument must be a list, got string`. `push` names its first
argument only, because its second is deliberately any value at all:
`push(xs, nil)` and `push(xs, [1])` are both ordinary.

This is the same shape as **Taking and dropping**, where `first` and `rest`
stay beside the `take` and `drop` that generalise them. A special case that
reads as itself is kept; a special case that only saves typing is not.

### What the fold costs

That `dedupe` is quadratic, and so is every other fold on this page. The
section has argued `push` against `concat` at length without saying so, and
the argument above is complete without it — but a reader who takes `push` on
that argument and writes the loop it is for should be told what the loop
costs.

**Both builtins copy, and so does `set`.** `push(xs, x)` builds a list of
`len(xs) + 1`, `concat(a, b)` one of `len(a) + len(b)`, `set(m, k, v)` a map
of `len(m) + 1`. That is not an oversight; it is what *nothing in Vine
mutates* means, and it is what makes a list safe as a map key — see
**Composite keys**. One copy is a copy. One copy per element is the square:

```text
reduce(xs, fn(a, x) { push(a, x) }, [])       0.15s  0.30s  1.06s  3.89s
reduce(xs, fn(m, x) { set(m, x, x) }, {})     0.19s  0.47s  1.68s
map(xs, fn(x) { x })                          0.03s  0.04s  0.04s  0.06s
```

at 8000, 16000, 32000 and 64000 elements. Doubling the input quadruples the
first two and does nothing to the third. `reduce(xss, concat, [])`, the
flattening this section offers as `concat`'s reason to exist, is the same
curve at a quarter the size: 0.04s, 0.08s and 0.25s at 4000, 8000 and 16000
one-element lists.

**`map` and `filter` are flat because they have no accumulator.** Each builds
its answer in one pass and never holds a partial one. A fold does hold one, by
construction — that is what a fold is — and Vine has no loop, so a fold is the
only way to build a container whose shape is not one-to-one with its input.
The cost lands exactly where there is no alternative spelling.

**So the shape to reach for is a map, not a longer list.** `dedupe` above asks
`contains(acc, x)` of a list that is growing, which is a scan inside a copy;
the same answer folded into a map is a hash lookup inside a copy, and the list
comes back out with `keys`:

```
let dedupe = fn(xs) { keys(reduce(xs, fn(m, x) { set(m, x, true) }, {})) }
```

Over 8000 distinct elements that is **0.13s against 9.37s** — the same list,
in the same order, seventy-two times faster. The order survives because a map's
keys are in the order they first appeared, which **Map order** already
promises and `set` on a key already present does not disturb. The two spellings agree on every pair and triple of the
value list in `tests/properties/no_traceback.py`, which
`tests/properties/composition_holds.py` enumerates.

**What the map spelling costs is a list holding a function.** A function may
not be a key, so `dedupe([fn() { 1 }, 1])` fails where the `contains` spelling
answers. That is the whole of the difference, it is the rule **Looking up a
key** states rather than a new one, and it is the reason both spellings are on
this page instead of one.

**These numbers are the implementation's, and they are not a promise.** What
the language fixes is that `push` answers a new list; how much of the old one
gets copied to do it is `vine/builtins.py`'s business, and a representation
with a cheaper append would change every figure above without changing a
single answer. What is closed is the shortcut that keeps the current
representation: appending in place when nothing else can see the list. The
accumulator of `reduce(xs, fn(acc, x) { push(acc, x) }, [])` is held by five
references at the moment `push` runs, one of them the binding of `acc` in the
function's own environment — a name the body is still free to mention. And
the case where it is safe and the case where it is not are indistinguishable
from the inside: `reduce(xs, push, [])`, where only the fold holds the list,
and `let xs = [1, 2]` followed by `push(xs, 3)`, where a live name does, both
count exactly three. So write a fold expecting the square, and do not write
one expecting it to be fixed.

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
it. Two more functions sit at the end of this section and neither is a third
conversion: a number can be written to a set number of decimal places, see
**Formatting**, and a string can be written with every character in it
visible, see **Revealing**.

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

**There is a second promise, and it is the narrower one: no control character
comes out as itself.** `repr` writes every C0 and C1 control as a codepoint
escape — `\u{0}` through `\u{1f}` and `\u{7f}` through `\u{9f}`, less the three
that already have `\n`, `\t` and `\r`. Sixty-two escapes, and that is exactly
the characters Unicode files under `Cc`. A string holding a record separator
therefore reprs as something a reader can type and not only paste:

```
repr("a\u{1e}b")                      # "a\u{1e}b"
```

That range and no wider, and the reason is the one **Text** gives for `len`
counting codepoints. Asking a Unicode table which characters are invisible
would catch the non-breaking space as well, and would make `repr(s)` — a value
a Vine program can compare, print and write into a file — depend on which
Unicode release the implementation was built against. `Cc` is the one set the
standard has closed forever; every wider notion of *invisible* is a table that
moves.

**So `repr` is legible and not unambiguous, and the difference is worth being
exact about.** Two kinds of character still come out as themselves and neither
can be seen. A non-breaking space is *confusable*: it occupies a column and
reads as a space. A zero-width space, a word joiner, a byte-order mark and the
rest of Unicode's format characters are *invisible outright* — they occupy
nothing, so `repr` of one is a line that looks like an empty string:

```
len(repr("\u{200b}"))                 # 3 — quote, a zero-width space, quote
repr("\u{200b}") == repr("")          # false — though the two print alike
```

That is the cost, it is real, and it is smaller than an answer that differs
between two machines running the same program. What `repr` promises is the
controls, which is a promise it can keep the same way twice; it does not
promise that every character in its output can be seen. A program that needs
that guarantee asks `reveal` for it instead — see **Revealing** below, which
is the same string with a wider escape set and is not the same value.

The first promise held through all of this and was never the whole of it: for
as long as `repr` of a record separator answered a line with one sitting inside
it, the output was source, read back `==`, and could not be read.
`tests/properties/repr_is_source.py` checks the first sentence and
`repr_is_legible.py` the second, over every codepoint a Vine string can hold.

**Functions are the exception, and the only one.** A closure is its parameters,
its body *and* the environment it captured; no expression denotes that. There
are two spellings, because there are two kinds of function and `type` calls
both `function`:

```
let twice = fn(x) { x * 2 }
repr(twice)                           # <fn twice/1>
repr(trim)                            # <builtin trim>
type(trim)                            # function
```

A builtin carries no arity because it does not have one number: `range` takes
one argument or two and `print` takes any. Neither spelling is parseable,
deliberately, so neither can be mistaken for source that would work.

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

### Revealing

The paragraph above says where `repr` stops. `reveal(s)` is where it does not:

```
let scraped = "east\u{a0}1"
let typed = "east 1"
scraped == typed                        # false
len(scraped) == len(typed)              # true
len(repr(scraped)) == len(repr(typed))  # true — and the two lines look alike too
reveal(scraped)                         # "east\u{a0}1"
reveal(typed)                           # "east 1"
```

That is the whole of what it is for. A scrape produces two rows a reader
cannot tell apart and `==` says are different; `len` agrees they are the same
length, `repr` writes two lines of the same width, and before `reveal` nothing
in the language said which character was the difference.

**It is `repr` plus one rule: a codepoint above U+007E is written as an escape
too.** `repr` already escapes everything below U+0020 and U+007F through
U+009F, so what `reveal` leaves as itself is exactly printable ASCII. Below
that ceiling the two are one function:

```
reveal("a\tb") == repr("a\tb")          # true
```

**Why it may be wider than `repr` when `repr` refused to be.** What `repr`
refused is a *table*. Every wide notion of *invisible* is a Unicode category,
a category is a property of a Unicode release, and `repr(s)` is a value a
program compares, prints and writes to a file, so an answer that moves under
it is a bug in the program that stored it. The ceiling here is not a category.
Printable ASCII is a range, it was frozen before Unicode existed, and no
release can move it — so `reveal` keeps the property the refusal was
protecting while being as wide as the complaint requires. **Text** draws the
same line between `repr` and `trim` from the other end.

**The quotes are part of the answer and not decoration.** A trailing space is
as invisible as a zero-width one, and no escape set that leaves printable
ASCII alone can show it. What shows it is the closing quote:

```
reveal("east ")                         # "east " — the quote is what shows the space
reveal("east")                          # "east"
```

**What it costs is every character above ASCII, including the ones nobody was
confused by.** An accented word and a zero-width space come out the same way:

```
reveal("caf\u{e9}")                     # "caf\u{e9}"
reveal("\u{200b}")                      # "\u{200b}"
len(repr("\u{200b}"))                   # 3 — quote, a zero-width space, quote
len(reveal("\u{200b}"))                 # 10
```

So `reveal` is not the everyday way to show a string and `repr` is not a
degraded one. This is **Formatting**'s shape: `str` writes a number the way
Vine writes it down and `fixed` the way a column needs it, and neither is the
general case of the other. Here the two readers are the one who wants to read
the text and the one who wants to know what is in it.

**A string and nothing else**, the way `fixed` takes a number and nothing
else. `str` and `repr` convert *any* value and which applies is decided by who
reads the result; `reveal` is not a third member of that pair, because the
question it answers is one only a string raises. A column is a list of
strings and maps — joined rather than printed as a list, since a list reprs
its elements and would escape every backslash a second time:

```
let rows = ["east\u{a0}1", "east 1"]
join(map(rows, reveal), " ")            # "east\u{a0}1" "east 1"
reveal(rows)                            # error: reveal argument must be a string, got list
```

**And it is a string at the prompt too**, which is the one place the answer
surprises. The REPL echoes a value the way `repr` shows it — see **The REPL** —
so a bare `reveal(s)` there is a revealed string being revealed a second time,
and every backslash doubles. `print` is what shows it once:

```
>>> reveal("east\u{a0}1")
"\"east\\u\{a0}1\""
>>> print(reveal("east\u{a0}1"))
"east\u{a0}1"
```

Nothing is wrong in that first line and it is not worth a special case: the
echo has one rule and this is it, applied to a value like any other. It is
written down because the prompt is where somebody reaches for `reveal` first.

#### Why a builtin and not a composition

**add what cannot be composed, refuse what can**, so here is the measurement.
`split(s, "")` already reaches the codepoints, and that is as far as Vine
goes: no builtin turns a character into anything that identifies it. `len` of
one is 1 whatever it is, `int` of one is an error, and `str` and `repr` hand
back the character that could not be seen in the first place.

```
map(split("east\u{a0}1", ""), len)      # [1, 1, 1, 1, 1, 1]
```

`int` of one is not a way round it either: it fails, and the failure is a
report rather than a value, so nothing in the program can read it. That
report does now write the string out in escapes -- **Conversions** has it --
which is this section's rule applied where a reader meets it rather than
where a program can use it.

What is left is `<`, which does order strings by codepoint, so a program can
compare a character against a literal it has already typed. That makes the
composition a hand-written list of suspects, and it answers only for the
characters on the list:

```
let suspect = split("east\u{a0}1", "")[4]
contains("\u{a0}\u{200b}\u{feff}", suspect)   # true — because a0 is on the list
```

A list of suspects is a guess, and the value of an answer here is that it is
not one. Nothing composes to the character that was *not* thought of, because
`\u{...}` is lexical — its digits are source, so no expression builds a
character from a number that was computed.

**Why not a codepoint number**, which is the other shape this could have had.
`code(c)` answering `160` would identify the character too, and would compose
further: arithmetic, ranges, sorting by codepoint. It is refused for now, on
two grounds and not on principle. It answers in decimal where every other
mention of a codepoint in this language — the escape, this section, the error
messages — is in hex, so a reader would convert by hand at the one moment they
are already confused. And the composition that gets from a list of numbers
back to something to *read* is the one Vine cannot write, since a character
cannot be built from a computed number. `reveal` is the debugging view; `code`
would be the arithmetic, and no program here has yet asked for arithmetic.

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
let total = 1.5
print("{total:.2f}")
```

```report
syntax error: expected '}' to close the interpolation, found ':'
 --> report.vine:2:14
  |
2 | print("{total:.2f}")
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
let label = "total"
print(label + 3)
```

```report
runtime error: cannot add string and int
 --> example.vine:2:13
  |
2 | print(label + 3)
  |             ^
```

A report may say more than that. Under the caret come any number of extra
lines, each labelled:

```
print("{")
```

```report
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
case in a session. Three entries typed at the prompt:

```
let greet = fn(first, last) { "{first} {last}" }
"an entry in between"
greet("solo")
```

```report
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

The line between the two is not quite *fact* against *rule*, and three
messages show where it really falls. `pow(2, n)` for an `n` no float can hold
says `pow converts both of its arguments to a float`, which is true of every
call to `pow` and is therefore a rule — and it is a **note**, because without
it the headline is a non-sequitur: the program named no float. So is `'+'
between an int and a float converts the int`, and so is `'{' inside an
interpolation opens a map literal, not an escaped brace`, without which
`expected ':' after the map key` is about a map the reader did not write.

A note is what a reader needs to understand **this** failure, whether that is
a fact about their program or the rule that caused it. A help is a rule they
may want **next**, and it would be just as true had they made no mistake at
all. That is why the float ceiling is a help on all seven messages that need
it, and `pow converts both of its arguments to a float` is a note on one.

A help belongs on every message whose complaint the reader cannot check by
eye. *Too large to be a float* is the case: seven messages say it — a
literal past the ceiling, `float()` of an int or of `"1e400"`, `pow` on
either side, an operator mixing an int with a float, and an arithmetic result
— and *how large is allowed* is a rule of the language rather than a fact
about the program, so each of them carries `the largest float is about
1.8e308`. It is one string in `vine/rules.py`, because three of the seven
used to say it in two different sentences and four said nothing at all.

Every message whose complaint cannot be checked by eye now offers a rule.
One was the exception for thirty-two ticks, and the shape of the exception is
worth keeping. `value nested too deeply to work with` wanted the depth
allowed and the language had none: **Bindings** called that a gap rather than
a decision, so a help reading *there is no fixed limit* would have printed a
hole in the voice of a rule and settled in a report a question nobody had
settled. Withholding it was right, and the fix was not to word it better. Tick
33 counted the depth, and the message the same program prints now has a number
in the headline and the rule under it:

```
let deep = reduce(range(1000), fn(a, i) { [a] }, [])
print(deep)
```

```report
runtime error: value nested more than 1000 deep
 --> report.vine:2:6
  |
2 | print(deep)
  |      ^
  = help: a value may nest 1000 deep; building a deeper one is not an error until something reads it
```

That split is the contract, not decoration. The caret is where the failure
was *detected*, which is not always where it was caused: a note may name the
cause, and labelling the two differently is what keeps a message from
guessing. `"{"` is the case that forced it — a string really did open at that
quote and never close, so the caret belongs there, and everything the reader
is missing is a fact about a different character.

**Where the failure came from** is the other thing one caret cannot say. A
function is written once and called from everywhere, so a true position
inside one is a place the reader did not choose to be looking at:

```
let mean = fn(xs) { reduce(xs, fn(a, b) { a + b }, 0.0) / len(xs) }
let hours = [1.0, 2.0]
let extra = []
print(mean(hours))
print(mean(extra))
```

```report
runtime error: division by zero
 --> mean.vine:1:57
  |
1 | let mean = fn(xs) { reduce(xs, fn(a, b) { a + b }, 0.0) / len(xs) }
  |                                                         ^
  = note: mean was called at 5:11
```

`mean` is correct, it is called twice, and the mistake is the empty list on
line 3. Without the last line nothing in that report is about the half of the
program the reader has to change.

Each call is a **note**, for the reason the split already gives: the position
is a call in the reader's own text, so it is a fact about this program rather
than a rule of the language, and it says where control came from rather than
guessing what was meant. They are innermost first, because the innermost is
the one the reader cannot work out — every position given is inside their own
program, so they can walk up from it.

Three calls are named and the rest are counted:

```
let d = fn(x) { x / 0 }
let c = fn(x) { d(x) }
let b = fn(x) { c(x) }
let a = fn(x) { b(x) }
print(a(1))
```

```report
runtime error: division by zero
 --> chain.vine:1:19
  |
1 | let d = fn(x) { x / 0 }
  |                   ^
  = note: d was called at 2:18
  = note: c was called at 3:18
  = note: b was called at 4:18
  = note: 1 more call is not shown
```

Two kinds of call are counted without being named. One at the caret's own
position is not a second place to look: `fn(n) { loop(n + 1) }` fails at its
own recursive call, and five hundred copies of that line would say nothing
the caret has not. One identical to the call just named is recursion, which
on a stack is the only thing it can be. What is left of runaway recursion is
the call that entered it and the depth, which is the whole of what the caret
was missing:

```
let loop = fn(n) { loop(n + 1) }
loop(0)
```

```report
runtime error: call depth exceeded 500 (infinite recursion?)
 --> loop.vine:1:24
  |
1 | let loop = fn(n) { loop(n + 1) }
  |                        ^
  = note: loop was called at 2:5
  = note: 499 more calls are not shown
```

The count is of calls and not of dropped lines, so a failure two hundred
calls down never reads like one at the top. A builtin is never named: it has
no Vine text to point at. A function a builtin called is named at the
builtin's own call, which is where that call came from, and under the same
label an arity error would use — `map([1], fn(x) { x + nil })` reports
`<anonymous> was called at` the `map`.

A report quotes a value the way `repr` writes it, which is the form a reader
of the program recognises: `a map of 2 keys has no key "thé"` and not a row of
escapes. Where that form is what makes a true message look wrong, the report
adds the value **written out in escapes** as a note -- see **Conversions**,
which is the only place the language can tell the two apart without
consulting a Unicode table. Everywhere else the reader has something better
than a rendering: a second position. The caret is on the token whose *kind*
the parser is objecting to, and a duplicate map key is reported at the second
of the two with the position of the first in a note, so neither message has to
say which of two values it means.

The two keys need not look alike. `{{a: 1, b: 2}: 1, {b: 2, a: 1}: 2}` gives
one key twice — order is not part of a map's identity, see **Composite keys**
— and the headline quotes the spelling under the caret, which is the second.
The spelling a map built with `set` would keep is the *first*, because **Map
order** keeps what the data first said. Quoting that one instead would set the
headline against its own caret, and it would buy nothing: both spellings are
already in the report, one under the caret and one at the position the note
carries.

Messages are written in Vine's words and never the implementation's. The
parser calls a token `ident`; nobody writing Vine has been told what that is.
The standard to meet is `index 5 is out of range for a list of length 3`:
what was asked for, what was there, and nothing to look up first.

**What was there** is a type when the operation does not apply to the value at
all, and a fact about the value when it applies and this argument is what
failed. `cannot index bool` is finished: nothing indexes a bool, so no index
would have worked and naming one would say nothing. `a map of 4 keys has no
key "z"` is the other case -- indexing a map is exactly the operation being
performed, it works for four other keys, and the type `map` is a fact the
reader already had. The same line separates `len expects a string, list or
map, got int` from `index 5 is out of range for a list of length 3`, and it is
the question to ask of a new message: *would this message be the same for
every argument of this type?* If it would, the type is the whole of what was
there.

That question is about **values**, and the parser's messages are not about
values. `expected ']', found the number 1` names one where the clause above
would ask for a type: no number closes a bracket, so every number is equally
wrong. But the type is the whole of what was *asked for*, not of what was
**there** — the token is the parser's reading of the reader's own text, and
the two can differ. `[1 01]` puts the caret under a `0` and says `found the
number 1`, because `01` is one token whose value is 1; `[1 1_0]` says the same
under the second `1`, because `1_0` is a number and a name and not one number.
A reader whose text was read differently than they wrote it has no other way
to find out, and quoting the token is the only line in the report that tells
them. So: a message about a value asks whether the type is the whole of what
was there; a message about a token quotes the token.

Two messages are deliberately short of it. `undefined name 'x'` does not say
what names are in scope, because the scope is the program's own text and the
reader is looking at it -- unlike a map, which is data and may have come from
anywhere. `cannot raise a negative number to a fractional power` names the
sign and the fractionality rather than the two numbers, because those are the
properties that caused it and no magnitude would have helped.

A Python traceback reaching the user is always a bug in the implementation.

Running a file exits 0 when the program runs and 1 when it fails, with the
report above on stderr. A problem with the command line itself — an unreadable
file, `-e` with nothing after it, or more than one program named at once —
exits 2 and is reported as `error: ...` with no position, because nothing has
been parsed to have a position in.

One command line runs one program. `vine a.vine b.vine`, and `-e` beside a
file, are refused rather than half-obeyed: running the first and ignoring the
rest exits 0, which reports success for the part that never happened.

### The rules a report may offer

Eighteen rules, and every help is one of them. Seventeen live in
`vine/rules.py` for the reason the float ceiling gives above: a rule written
at the raise site that needed it is found only by someone already standing at
that raise site, and the next message to need it is somewhere else. Each is
listed against the section that states it at length, because a help is a
reminder of this document and never a replacement for it.

The eighteenth is the command line's, and it is elsewhere because a problem
with the command line has no position and so no report to hang a help on —
`vine/cli.py` spells the ` = help: ` prefix out by hand rather than rendering
it. It is a rule offered for the same reason as the other seventeen, so it is on
the same list.

- `the largest float is about 1.8e308` — **repr and str**
- `every float is finite; the largest float is about 1.8e308` — **repr and str**
- `the digits are 0 to 9, optionally signed, with spaces, tabs or newlines around them` — **Conversions**
- `a default answers for text that is not a number, and for nothing else` — **Conversions**
- `the smallest float is 5e-324, which has 1074 decimal places; nothing has more` — **Formatting**
- `there is no exponent operator; x to the power y is pow(x, y)` — **Operators, loosest binding first**
- `a line ending in an operator continues onto the next; only '|>' continues from the left` — **Lexical structure**
- `only a function body may return; a block's value is its last statement` — **Early return**
- `a negative index counts from the end, but a count does not` — **Taking and dropping**
- `to give a key a new value, use set(m, k, v)` — **Map order**
- `a key may be any value that holds no function` — **Composite keys**
- `the escapes are \n \t \r \" \\ \{ \} and \u{...}` — **Lexical structure**
- `a codepoint is written '\u{1e}' -- hex digits in braces` — **Strings**
- `'\u{d800}' to '\u{dfff}' are reserved and are not text; a string holding one could not be printed` — **Strings**
- `a literal brace is written '\{'` — **Strings**
- `a hole holds one expression, with no format after it; for decimal places write "{fixed(x, 2)}"` — **Formatting**
- `a value may nest 1000 deep; building a deeper one is not an error until something reads it` — **Bindings**
- `vine's options are -e, -h/--help and -v/--version; any other argument is a file name` — **Running it**

The list is exhaustive in both directions, and `tests/properties/help_roster.py`
is what holds it there. A rule Vine prints and this list does not name is an
undocumented rule; a rule named here that no program can print is one whose
message was deleted or reworded with the document left behind. Neither is
visible in a golden file, because a golden is a copy of the message it checks.

## Not in v0.2

Deliberately absent, roughly in the order they look worth adding: a
module/import system, a `match` expression, user-defined operators, and a
bytecode compiler. Anything here is fair game for a later tick — but adding
one means adding its tests and updating this file in the same commit.

Early `return` was the fifth, at the head of the list, from tick 1 until tick
26 took it. What took it was not an argument: it was running the flattening
that would have made it unnecessary and watching it fail on an empty list. See
**Why `return` earns its keyword**. The other four have now been confirmed
absent by seven ticks without one of them being argued either way, which is
what a question looks like once it has stopped being asked. Whoever reopens
one: the cheapest move is to write the program the feature is for, in the Vine
there is, and read it.

Audited in tick 7, rechecked in ticks 21 and 26: the remaining four are
absent. `import` is not a keyword, so `import "x"` is two statements on one
line and says so —
`expected end of line between statements, found the string "x"`. `match` is
not a keyword either, so `match x { 1 => 2 }` fails at `x` for the same reason
and never reaches the `=>`; tick 7 wrote that it failed *at* the `=>`, which
was a guess at a parser that stops earlier than it thought. There is no syntax
that binds an operator, and `vine/interp.py` walks the tree. No case guards
any of this, deliberately — a test that a feature is missing passes for as
long as nobody is working on it, and fails on the branch of whoever is, which
is the one place the reminder is noise rather than news. The paragraph above
is the reminder, and it is aimed at the right reader.
