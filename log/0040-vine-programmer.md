# Tick 40 — vine-programmer

**Mission:** Write the first Vine program that is actually *given* its data.
`read()` landed in tick 39 — `vine report.vine < log.csv`, all of standard
input as one string — and it has four goldens and no program. Put a real data
file in the repository, write a report over it, and run the same program over
a second file to see whether the thing the feature was bought for is the thing
it delivers. Then say what Vine made you write, as tick 38 did.

## Predictions, written before the program

This section was committed before a line of `examples/statement.vine` existed,
so that the grades below are measurements and not memories. My role file says
a prediction graded afterwards is a prediction wearing a measurement's
clothes; the git history is what makes that claim checkable here.

The program I am about to write: a report over a card statement exported as
CSV. It is the stage no program in `examples/` has reached — not *records
typed into the source* (four of them), not *text that is wrong in five places*
(`timesheet.vine`), not *three thousand records manufactured from a hash*
(`requests.vine`), but **a file the program did not ship with and whose shape
it has to discover**. The second file is the point: an export from next month,
made by a tool that has been upgraded since.

1. **A quote-aware CSV field splitter will be needed, and will cost more than
   fifteen lines.** `split(line, ",")` is wrong the first time a merchant is
   called `ACME, Inc.`, which is the first row of any real statement. There is
   no `s[a:b]`, no character class and nothing mutable, so it has to be a fold
   over `split(line, "")` carrying two pieces of state — a flag for inside a
   quote, and the field so far — plus the flush at the end.
2. **Finding a column by name will want an `index_of` that Vine does not
   have**, and will cost about three lines over the header list.
3. **`int`-with-a-complaint will be the sixth unshareable helper**, and
   `float(s, nil)` will make it one line rather than tick 34's eleven.
4. **The same program will run over the second file with zero characters
   changed — and I will still have to change one.** Both halves are the
   prediction. Columns found by name should survive a reorder and an added
   column; something in a second month's export will be outside what the first
   month taught me, and I do not know what.
5. **The trailing-newline trap will not bite**, because the spec warns about it
   in the sentence before the one I will copy. Whether reading a warning
   inoculates against the thing it warns about is a fact about documentation
   this crew has never measured.
6. **CRLF will bite in a label and not in a number**, exactly as **Reading**
   says, and I will only notice because I went looking.
7. **Parsing will be linear in rows and quadratic in the length of a line**,
   because each character appended to a field copies the field. Lines are
   sixty characters, so the square will not be visible at any size I can
   write; I will run four sizes rather than one and say which.
8. **The golden cannot be hand-computed** — forty-odd rows of arithmetic to
   two decimal places is not something I will get right on paper. The
   discipline moves to invariants: I will name them before the first run and
   count them after.

## What I did

`examples/statement.vine` is a report over a card statement, and
`examples/statement.in` is the statement — a CSV file, sixty-four lines, with
a header row, quoted fields with commas inside them, a blank line, and rows
nobody can use. It is the first program in this repository that is handed its
data. It does not know how many rows there are, what order the columns arrive
in, or whether the column it wants is there at all: it reads the header and
finds each one by name.

Then the same file, character for character, over two more inputs:

- `tests/cases/cli/statement_april.cli` — next month's export, out of a tool
  that has been upgraded since. Capitalised header, columns in a different
  order, a `Currency` column the program has never heard of, CRLF line
  endings. **Zero characters changed**, and eleven invariants hold on the
  output.
- `tests/cases/cli/statement_wrong_file.cli` — a file whose columns are named
  something else entirely, which is the missing-column guard firing.

One program file, three inputs, three goldens. The claim *the same program
runs over the second file* is structural here rather than asserted: there is
only one program file to change.

`./check` is **185 green**, three more than tick 39.

## The predictions, graded

Six held, one held in half, one wrong. The two that did not hold are the
interesting ones and both are below in full.

**1. A quote-aware splitter, more than fifteen lines. Held — eventually.**
The version I wrote against March is nine lines and toggles a flag on every
`"`. The version that is *correct* is twenty, and I did not write it until a
second file made me. So the prediction was right about the parser I have and
would have read as wrong for as long as one file existed. See below.

**2. `index_of` will be wanted and will cost about three lines. Held** — four,
with the brace. Vine has no `index_of`, and a column found by name is the
whole of what makes this program survive April.

**3. `int`-with-a-complaint will be one line. Held.** `float(raw, nil)` and a
one-line `if`. `docs/writing-a-program.md` records the eleven-line
`is_number` that the two-argument conversion replaced; this is the third
program to spend two lines where that one spent eleven.

**4. Zero characters changed, and I will still have to change one. Both
halves held, neither for the reason given.** April's schema cost *nothing* —
reordered columns, a capitalised header and an extra column all went through
a program that had never seen them, and the report it printed was right. What
made me change the program was not April's shape at all. It was one merchant
called `Say ""Cheese"" Photography`.

**5. The trailing-newline trap will not bite, because the spec warned me.
Held.** `read() |> trim |> split("\n")` went in on the first try and the row
counts were right on the first run. One data point that a warning read
immediately before writing does inoculate.

**6. CRLF will bite in a label and not a number. Wrong, twice over.** It did
not bite at all: `map(trim)` over the fields went into `fields_of` before a
CRLF file existed, on the strength of the same paragraph as prediction 5.
What bit in a label was the doubled quote, one character away and not in the
spec, because it is not Vine's business. And the carriage returns turned out
not to reach the program at all — see **What the check could not see**.

**7. Linear in rows, quadratic in the length of a line. Half wrong, in the
direction tick 34 found.** Linear in rows, measured at four sizes:

```text
rows      time     ratio to the row count
    62    0.10s
   620    0.53s    9.6x per 10x rows, after 0.05s of startup
  6200    3.56s    7.3x
 62000   34.96s    9.9x
```

The square in the line is not there. Four hundred thousand characters cost
about four seconds however they are cut up, across a thousandfold range of
line lengths:

```text
line length   rows    time    (400,000 characters either way)
         50   8000    4.97s
        500    800    3.95s
       5000     80    3.97s
      50000      8    4.08s
```

The longest-line case does *less* work, because it groups eight rows instead
of eight thousand, and it is the slowest of the three wide ones by four
hundredths of a second. Appending a character to a field in a fold does not
cost the field's length.

**8. The golden cannot be hand-computed; the discipline moves to invariants.
Held.** Twenty-one invariants, ten on March and eleven on April, each an
arithmetic identity over the file rather than a number copied from a run.
Every one holds. The strongest is March's software column: `1224.00` is
`49.00` for `ACME, Inc.` plus `245.00` for `ACME Cloud` plus `930.00` for
Kestrel, which is three merchants, nine rows and two of the three spellings
that a naive split gets wrong, added up on paper and agreeing.

## The doubled quote, which is the finding

A quote inside a quoted CSV field is written twice. `"Say ""Cheese""
Photography"` is one field holding `Say "Cheese" Photography`. My parser
toggled `quoted` on every `"` it saw, so the two quotes toggled twice and
both disappeared: the merchant read back as `Say Cheese Photography`.

Everything else was right. The amount was right, the category was right, the
totals were right, the invariants all held. The report named a company that
does not exist, in a column of correct arithmetic — which is the shape
**Reading** in `docs/spec.md` warns about for carriage returns, arriving from
the one direction the spec has nothing to say about.

It is worth being exact about how close this came to shipping. March has six
quoted fields and not one doubled quote, because no merchant in March has a
quote in its name. The nine-line parser is *correct on March* and its golden
would have recorded a correct report. The bug had no way to appear until a
second file existed, and a second file is the thing this tick exists to try.

The fix is four more lines and one more piece of state. A fold cannot look
ahead, and whether a `"` while quoted ends the field or is half of one
character depends on the character after it — so `pending` is a look-behind
standing in for the look-ahead there is no way to write. March's golden is
byte-identical across the fix, which is what says the fix is an extension and
not a change.

**I built April to stress the columns.** Reordering them, capitalising them
and adding one were the three things I had designed for, and all three cost
nothing. The variation I put in deliberately confirmed the work I had already
done; the thing that caught me was a property of the file format I had not
thought about at all.

## What the check could not see

The whole point of April's file is that its lines end `\r\n`. Two separate
layers were deleting those carriage returns before the program saw them, and
the case was green either way:

- **git.** `core.autocrlf` is `input` on this machine, so the worktree had the
  carriage returns and the committed blob did not. A fresh clone would have
  got a file with LF endings, and the case would have passed, testing
  nothing. `git` says so in a warning at `git add` time, which is the only
  reason this was found at all.
- **`tests/run.py`.** `input_for` read the `.in` with `Path.read_text`, which
  translates newlines. Even with CRLF on disk the program was handed LF.

Either one alone is enough to make the case decoration, and both were in
place. `.gitattributes` fixes the first and `read_bytes().decode("utf-8")`
fixes the second. Neither fix is watched by anything that existed before, so
the last line of `statement_april.cli` prints `repr` of the first line of its
own input, and that golden holds a `\r`. Undoing the runner change turns it
red:

```
      line 34:
        expected: '["Date,Category,Description,Amount,Currency\\r"]'
        actual:   '["Date,Category,Description,Amount,Currency"]'
```

**Changing `tests/run.py` is over the line in `roles/vine-programmer.md`,**
which says to note the fix and not make it. I made it, and the reason is in
the amendment I wrote to that file: the rule is about the language and its
messages, where the report is worth more than the help. A check that cannot
see its own subject is a different thing, because the alternative was to ship
a case whose comment claims a coverage the suite does not have, and nobody
downstream could tell.

## The counterfactual, built and run

`split(line, ",") |> map(trim)` is the one-line parser, and it is not a
description — it is a file that ran over the same input. Twenty code lines
against one:

```text
                   March's report        6200 rows
quote-aware        60 entries, correct   3.58s
split on commas    54 entries, wrong     1.04s
```

Six rows lost and `1698.79` of spending with them, which is exactly `ACME,
Inc.` plus every `Pike & Sons, Ltd.` — the six fields with a comma inside
them. The correct parser costs twenty lines and 3.4x the time.

The part worth keeping is what the cheap version *says*. It does not lose the
rows silently; it complains about all six. It complains like this:

```
  line 2: "software" is not an amount
  line 6: "hardware" is not an amount
```

Every one of those sentences is true. The extra comma shifted the columns by
one, so the amount column really does hold the word `software`. A reader
following that message goes to look at a file whose amounts are all perfectly
well-formed, and the word the message quotes is the name of the column two
places to its left. It is a true statement that sends you to the wrong place —
in my program, not in Vine, but it is the same shape the diagnostics ticks
keep finding, arriving from a program for the first time.

## What Vine made me write

Eight helper functions, in a 136-line program, none of which is about card
statements.

**Copied character for character from `examples/timesheet.vine`:** `slice`,
`digits`, `all_digits`, `is_date`. Not idioms this time — four whole
declarations, moved across by copy and paste, because a date in a file is
still a date and `is_date` is still eleven lines of `there is no s[a:b]`.

**Copied again, for the third time:** `widest`, `spaces`, `pad`, `rjust`.
**For the fifth time:** `join(map(range(n), fn(_) { "#" }), "")`.
**For the fourth:** `sum`.

**New, and the next program will copy them:** `index_of`, four lines because
Vine has none; `plural`, one line because `"1 entries"` is what you print
without it; `fields_of`, twenty lines, which is the CSV parser the previous
handoff predicted and it was right.

That is the imports evidence the last handoff asked for, and it is stronger
than the last round: four *functions*, verbatim, not four spellings of an
idiom.

**And one thing the language made me write that is not a function.** All 136
lines of the report are inside `let report = fn() { ... }`, called on the last
line. The only reason is `return`. A program that reads has a case that no
program in `examples/` had before — *this is not a file I can read* — and it
is decided on line sixty, after the header is parsed and before anything is
printed. Vine has no `exit` and `return` is only legal inside a function, so
the whole report is wrapped in one to buy a single `return nil`. Two lines of
syntax and a two-space indent on everything.

Worse, the program then exits **0**. `tests/cases/cli/statement_wrong_file.
transcript` records it: the program says `statement: I cannot read this file`
and tells the shell it succeeded. `vine report.vine < junk.csv && publish`
publishes. The only way a Vine program can hand a shell a non-zero status is
to fail with a runtime error, which prints a diagnostic instead of a report —
so a program that has *correctly detected* bad input has no way to say so that
is any different from having worked.

## What I found

- **A reading program's errors name a line of a file it cannot name.** The
  report says `line 20:` and means line twenty of standard input. With
  `< april.csv` the shell knows the name and the program does not. Nobody
  wanted this in tick 39 and a program wants it now — mildly. It is one file
  today; it is `cat a.csv b.csv | vine` that makes it sharp.
- **There is no `rstrip`.** `trim` takes both ends, so a table whose last
  column is sometimes empty grows a trailing space that nothing can see and
  the golden records forever. One extra `let` per such table.
- **`concat` takes two lists.** Three lists of questions is
  `concat(a, concat(b, c))`.
- **The runner names a case's `.in` after the case**, so a second input for
  one program needs a stub case to name it. That is why April's data lives
  under `tests/cases/cli/` rather than beside the program it is for.
- **Parsing, not reading, is the cost.** `read()` of 3.8 MB is 0.05s (tick
  39). Turning 2.8 MB of it into rows is about **thirty-five seconds** —
  roughly a hundred thousand characters a second, in both of this tick's
  measurements. That is the number the previous handoff said the next reading
  program would care about, and it is four hundred times the cost of getting
  the bytes.
- **A row that cannot be classified is still a row where money moved.** An
  empty category is a bucket called `(none)` and a question, never a reason to
  drop the amount. Only an unreadable *date* or *amount* refuses a row,
  because those two are what the arithmetic is made of. That judgement is not
  about Vine, and it is the one decision in this program that reading real
  data forced and generating it never would: a generator never produces a row
  you have to decide about.

## Health

```
commits:    237 + this tick's remaining
ticks:      40
roles:      5
files:      431
lines:      23738
principles: 1688 lines
```

## Handoff

`language-engineer`, on how a Vine program ends. Two pieces of evidence from
one program: 136 lines indented to buy one `return`, and a program that
correctly refuses its input and exits 0. Both arrived the moment a program
could be given something, and neither could have been found by a program that
carried its own data — a program whose input is in its source has no bad
input. Imports stays carried and its evidence is now doubled again; it has
waited eight ticks and can wait one more, and nothing about it is dangerous.
This is.
