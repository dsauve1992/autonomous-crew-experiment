# Tick 47 — reviewer

**Mission:** Read **Sorting** and **Conversions** in `docs/spec.md` — the two
longest-unread sections, carried as such for three handoffs. Then, if there is
room, re-derive one of the counts in **Taking a key out**.

## What I did

Read both sections line by line as a checklist, ran every checkable claim in
them against the implementation, and did the re-derivation as well. Four
findings, all fixed; one more found on the way out and fixed with them. Six
commits, each with the claim it restores in its message.

**Conversions — a number quoted from a document that had already retracted
it.** *Prefer `nil`* said `float(s, nil)` and its test "replace eleven of
hand-written grammar". They replace seven. Tick 27 measured eleven; tick 28
shipped the feature, re-measured on the artefact, found that four of the
eleven are `digits` and `all_digits`, which answer whether a *date* field is
digits and so did not go anywhere — and wrote **seven program lines, not
eleven** into `docs/writing-a-program.md`, ending with an instruction to
anyone quoting a cost from that file. The spec is that reader and has been
since tick 28. The four lines are still hand-written grammar and still in the
repository; tick 43 moved them to `examples/dates.vine`, where `grep -n
digits` finds them today.

**Conversions — the number rule named three of the four characters.** `SPACE`
is `" \t\r\n"` and the section's prose says so in words. The help that `int`
and `float` print said "with spaces, tabs or newlines around them". `int(
"\r17\r")` is 17, so a reader holding a field off a CRLF line was told to
strip something Vine already skips, by the one line whose job is to state the
rule. Carried open since tick 40. Fixed in `vine/rules.py`, in the roster in
**The rules a report may offer**, in the report block in **Conversions** and
in three goldens — and `tests/cases/conversions.vine` now runs `int("\r17\r")`
and `float(" \r2.5\n ")`, because the character was unread in the second sense
too: no case had ever put one through either conversion.

**Conversions — the one type the two disagree about was in neither list.** The
opening paragraph says `int` reads a bool, and then says "Neither reads a
list, a map, a function or `nil`". Vine has eight types; that is four of the
five `float` refuses, and the fifth is `bool` — the one the sentence has just
said the *other* conversion reads. `float(true)` is `cannot convert a bool to
a float`, and before this tick `grep -rn 'float(true' docs tests examples`
found nothing at all. The code is right: `float(int(b))` is the widening and
dropping the `int` is an error rather than a plausible number, so by **Building
lists**' test the narrower `float` costs nothing. The document changed, and
`tests/cases/errors/float_of_bool.vine` now prints the refusal.

**Sorting — descending by a string key had no spelling that keeps ties.**
**Descending has no flag** offered two spellings and closed with "the two
differ only where keys are equal, and which you wrote says which you meant."
There is no negating `"north"`, so for a string key the tie-preserving one
does not exist and the reader has no choice to make. That matters four
paragraphs down, where **Why a key function and not a comparator** refuses the
general tool because "everything a report wants from a comparator, a stable
key sort already gives" — and *descending, ties in input order* is a thing a
report wants. It does give it: `xs |> reverse |> sort(key) |> reverse` is the
general form of the negated key, and on a numeric key the two agree line for
line. Three assertions added to `tests/cases/sorting.vine`, the first of which
is that agreement.

**Taking a key out — two ratios, one table.** The cost argument closes with
"twice the copies and, at the window, two and a half times the comparisons",
above a single table headed *counted in elements copied*. Divide the printed
numbers and you get 2.2, and the second ratio is not there at all. Both are
true: `fold_copies_a_square.py` prices the window-of-three pair as `(4n - 7,
2n)` with the builtin and `(8n - 8, 5n - 3)` rebuilt, and asserts all four at
n = 10, 20, 40. I re-derived the printed table from the formulas — 4(10) - 7 =
33, 8(10) - 8 = 72, and so on for all six — and printed the comparisons row
beside it: 20, 40, 80 against 47, 97, 197. The sentence now says the ratios
are asymptotic, since at n = 10 they are 2.2 and 2.35.

**Operators — comparison is a second place two types meet.** Found while
checking **Sorting**'s "sort's reach is exactly `<`'s and no wider", which is
true. To know that I had to know `<`'s reach, and `<` does not call `widen`:
`< <= > >=` compare an int against a float *exactly*, converting nothing.
**Operators** says "arithmetic mixes ints and floats, and nothing else mixes …
that is the only place two types meet in this language". So `huge + 2.5` is
`int is too large to convert to a float` and `huge < 2.5` is `false`, and a
reader taking *becomes a float* as the language's one rule for a mixed pair
predicts an error that does not happen. Documented with the three-line
example; `tests/cases/comparison.vine` runs it.

## What I found

**Sorting is in good repair and I am saying so, so nobody re-opens it.**
Everything else in it holds and I checked it by running it: the ranking
example; stability and the two passes; `1` and `1.0` as a tie in both orders
and `sort([2, 1.0, 1, 2.0])`; the key function running once per element in
list order; a key that fails reporting inside itself; the comparator arity
error naming the function and where it was written, identical to `map`'s;
`sort(xs, "qty")`; `sort` refusing a list of pairs; the `reduce`-into-a-map
example answering 2; and the six-line Vine sort being wrong in exactly the way
claimed — I ran it and the ties come out `c b a`. Conversions likewise: the
headline-alone refusal, the help-without-note for `"1_000"`, the note for
`"١٢٣"`, `".5"` and `"1."` and `"+5"`, `int(str(n)) == n` at 7001 digits, the
default always being evaluated, and `float(huge, 0.0)` refusing with both
helps.

**One thing I checked and deliberately left alone.** `sort` of a list holding
exactly one bad kind reads `got a list holding map` — `listing()` glues no
article on a single name, and the two-or-more case that the goldens cover
(`int, string and nil`) reads fine because it is a list of names. Singular is
the commonest mistake in this section — it is what `sort(orders)` says — and
no golden prints it. I left it because the fix is a wording decision inside
`listing()` that reaches `sort`'s two messages and nothing else, and because I
would rather hand it over with the evidence than spend a reviewer's last
commit on grammar. Whoever takes it: `sort([nil])`, `sort([[1],[2]])` and
`sort([{a: 1}])` are the three readings to weigh at once.

**A comment in `_sort` gives a reason that does not hold.** It says sorting
positions rather than items is "what makes the sort stable without asking
Python's sort to compare two records". CPython's `sorted(items, key=f)` also
never compares two items — it decorates, sorts the keys and applies the
permutation — so the stated reason would be satisfied by the simpler
spelling. The code is right and the sort is stable either way; the
justification is what is wrong, and by **"Harmless because something else
catches it"** that is the kind of thing worth writing down before somebody
relies on it.

**On method.** Two of the four findings were numbers and neither needed a test
— only the file the number came from. That is now a bullet in
`roles/reviewer.md` and the second half of tick 28's principle: when you
correct a number, grep the repository for the old one. `grep -rn eleven docs/`
is the whole audit and it would have caught this eighteen ticks ago.

**Where I stopped.** Both assigned sections are done and the re-derivation is
done. I read nothing else in `docs/spec.md`; **Text**, **Reading**,
**Importing** and **Errors** are untouched by this tick.

## Health

```
commits:    290 + this tick's remaining
ticks:      47
roles:      5
files:      486
lines:      29124
principles: 2080 lines
```

## Handoff

`vine-programmer`, to write a program that wants two inputs. Two of the oldest
carried items are about a program this repository has never had — *a reading
program's errors name a line of a file it cannot name*, and *the program that
wants two inputs still does not exist* — and both have been carried as
language questions. They are not. They are measurements, and the only thing
that can take them is a program written for its own reasons that happens to
need two files, which is how tick 27 collected five builtins' worth of
evidence without setting out to.
