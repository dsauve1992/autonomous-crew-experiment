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
