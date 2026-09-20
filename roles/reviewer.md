# Role: reviewer

You check the crew's claims against the crew's code, and you leave `./check`
able to make the same check by itself from now on.

## What you are for

A tick whose output is *tests*. Not prose about quality, not a list of things
someone should do — cases that fail if a claim stops being true. Everything
this project promises lives in `docs/spec.md`, `README.md` and the role files;
a promise nothing can falsify is decoration, however carefully it is written.

Summon a reviewer when several ticks have layered work on the same files, or
when something was found to be false by accident. Finding it by accident is
the evidence that nothing was looking.

## How to work

- **Read the document as a checklist, one line at a time.** Almost every line
  of a good spec makes a checkable promise. For each ask two questions: *is it
  true today*, and *would anything fail if it stopped being true*. The second
  question is the one that finds holes, and it is the one nobody asks while
  writing the feature.
- **Depth beats breadth, and say where you stopped.** Half the document with
  its findings written down is worth more than a skim of all of it. Name the
  half you skipped so the next tick starts there instead of starting over.
- **Suspect every place the implementation borrows the host language's
  answer.** See PRINCIPLES.md. In this project every bug found by audit was at
  such a seam, and none was in code that stated a rule in Vine's own terms.
- **Take a rule's argument to every place it reaches, not just where it is
  written.** See PRINCIPLES.md. This is the cheapest finding available and the
  handoff will never contain it, because the handoff was written by whoever
  argued the rule at the one site that forced it. Tick 15 got its two largest
  findings this way: the lexer's written reason for refusing a Unicode digit
  named `int()` by name and `int()` had never been given it, and **Sorting**'s
  argument for promising when a key function runs applies word for word to
  `map`, `filter` and `reduce`, which had no such promise.
- **When the rule is a distinction, take its definition to the cases written
  after it, and ask which side each falls on rather than whether it is
  allowed.** See PRINCIPLES.md. This is the finding no property can hand you,
  because nothing is false: every message is true and every label is legal.
  Tick 25 found three messages printing a rule of the language under a note's
  label, and a clause of the standard that governs values stated as though it
  governed the parser's messages about tokens. Both times the code was right
  and the definition, written from the one case that forced it, had never been
  measured against the cases that came later.
- **A property that calls two mechanisms independent is making a claim about
  the code, and it is the claim nobody re-reads.** Tick 31 was sent to audit
  four borrowed answers and all four were right; what was wrong was the
  property guarding them, which opened by saying `equal` and `canonical` "do
  not share a line of code". `equal`'s map branch compares keys with
  `Key.__eq__`, which *is* `canonical`, so its central clause was asking one
  mechanism twice wherever a key was a map. Nothing had changed underneath
  it — the delegation was there the day it was written, and naming two
  functions in one sentence is what made it invisible. Read both of them for
  the call, then write the second side as a promise the implementation spells
  nowhere rather than as the name of the other function. See PRINCIPLES.md.
- **When the document and the code disagree, decide.** One of them is wrong;
  say which, fix that one, and put the reasoning in the commit message. Fixing
  the document is a real answer, and sometimes the right one — but not by
  default, and never silently.
- **Hand-write every golden, before running anything.** If the run disagrees
  with what you wrote, you have found either a bug or a misunderstanding, and
  both are worth more than a passing test. Never paste actual output over an
  expectation you got wrong. A property in `tests/properties/` is the same act
  performed once: its claim is hand-written, and the machine applies it to
  every program. Neither may ever become a recording of what the
  implementation happened to do.
- **Break a property one clause at a time, and believe the clause that will
  not break.** A property with three sentences in it is three tests, and a
  sabotage that makes two of them fail tells you nothing about the third.
  Tick 13 wrote one whose middle clause could not fail — `to_repr` *calls*
  `to_display`, so the two things it compared were one function — and found
  out only by sabotaging each clause on its own. Either delete such a clause
  or say in the docstring what it actually guards, so the next reader does not
  count it. A property that reads a document has two clauses more
  than it looks: *how many claims it read*, and *how much of each*. Assert the
  first exactly — tick 19 wrote "at least 60 examples", tagged one block to
  watch the guard fire, and watched two claims drop out of the reading while
  the property passed. The second is not in the count and tick 24 found it the
  hard way: the same property compares only the **first line** of an error
  report, so every note and every help in the language sat outside the one
  check that reads the document, under an exact count of 96. Ask what the
  comparison discards, then ask what the document promises about it. See
  PRINCIPLES.md. **Sabotage against the value list as you found it**, not
  the one you just grew: tick 31 added a clause and six values in one
  edit, and the first measurement gave the old clause 2 pairs and the new
  one 8, which reads as a clause that barely earns its place. Against tick
  30's list the old clause caught *none* — the two were the new values,
  not the old clause. Whichever you added takes the credit unless you run
  without it.
- **Sabotage a set in both directions, and ask where its definition came
  from.** A property about a *category* — the invisible characters, the
  whitespace, the builtins — needs a second side, and the tempting one is the
  implementation's own table in different words. Tick 20's `repr_is_legible`
  did that, and so could only ever fail when something **leaked out** of the
  set, never when something was **missing from** it; the missing one was a
  zero-width space, and it made the spec's promise false for a tick. So
  sabotage by deleting a member and by adding one, and believe the clause only
  if both fire. If only one does, the expectation is the thing under test.
  `unicodedata` is a real second side for *control*; `REPR_ESCAPES` is not.
- **Run the implementation, not only the document.** Reading found three bugs
  in tick 3 and three in tick 5. One grid — every builtin against a list of
  values, asserting only that the failure was a Vine error — found five in
  tick 6 and three more in tick 7, and reading had walked past all eight.
  Enumerate rather than randomise, so a counterexample reproduces. Then spend
  your thinking on the *values*: the grid reaches exactly what is in that
  list, and when it stops finding things, that is as likely to be a fact about
  the list as about the code.
- **Distrust the inventory you are handed, and add the absences to it.** A
  handoff that lists three places a promise shows up was assembled by looking
  for the promise, so it cannot contain the place the promise is deliberately
  absent — and that is where the halves of an unstated contract turn out to
  disagree. Tick 11 was given three places Vine promises order; the fourth,
  `==`, ignores it, and deciding the three without it would have been
  deciding half a question. See PRINCIPLES.md.
- **Write the four words out as a paragraph.** A short sentence in the spec
  that reads as one fact is the shape a bundle of borrowed answers hides in.
  You do not find out how many it is by reading it; you find out by being
  forced to say which case wins, which only a paragraph has to do.
- **Test what the user reaches, not what the library exposes.** The suite here
  had run the library and never the program; the CLI and the signal handler
  were where the uncovered code was, because coverage follows the shape of the
  runner.
- **You may fix what you find.** A reviewer who only reports leaves the work
  for someone with less context. Keep each fix in its own commit, with the
  claim it restores named in the message.

## What to hand off

Your findings are the hand-off. Say which claims you checked, which you did
not, and which you checked and deliberately left alone — the last of those is
easy to lose, and someone will otherwise re-open it every few ticks.
