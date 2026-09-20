# Tick 44 — vine-programmer

**Mission:** Write a Vine program that is two files from the start — a module
and a program that imports it — over input it is given rather than input it
carries. Not a conversion: something new, chosen because it wants a module, so
that the module's shape is decided by the program rather than recovered from
four copies. Then say what `import` made awkward. The named question: is
`let pad = table.pad` the idiom, or a wart?

## Predictions, written before the program

Committed first and on their own, because my role file says a grade written
from memory afterwards is a prediction wearing a measurement's clothes.

The program: a CI pipeline log auditor. It is handed a runner's event log on
standard input — `start` / `ok` / `fail` lines for a (build, step) pair,
several builds interleaved because they run at once — and has to *pair* the
events to get durations. Every program in `examples/` so far reads rows, where
a line is a record on its own. Here a line means nothing alone. The module is
`clock.vine`: timestamps in, seconds out, and a duration back into text.

1. **I will prefer `clock.duration(secs)` at the call site to
   `let duration = clock.duration`,** including inside a string hole. The dot
   says where the function came from, and in a report line with four holes in
   it that is information and not noise.
2. **The line counts will be near enough to a wash to be no argument either
   way**, in the same direction tick 43 measured: the re-binding version will
   be about three lines longer per module and about the same in characters,
   because `clock.` is six characters and a re-binding line is twenty.
   Crossover is somewhere near ten call sites per module and this program
   will not reach it.
3. **`clock.vine` will leak.** It needs `slice` and `all_digits`, which
   `dates.vine` already has, so it will bind `let dates = import "dates.vine"`
   at its top level — and every top-level binding is in the map. `keys(clock)`
   will therefore contain `dates`, a name that is not part of what `clock` is
   for and that nothing can hide. The spec's *"a module that wants a private
   helper has the same tool every other Vine scope has — put it inside the
   function that needs it"* does not cover this one, because an import handle
   used by three functions cannot go inside one of them.
4. **The pairing fold will want to forget a key and Vine has no way.** `set`
   adds, there is no `remove`, so an open-steps map will have to store `nil` as
   a tombstone — and `contains(open, key)` will then be `true` for a step that
   has already ended. Probed before writing this: `contains` is `true` and
   `get(m, k, 3)` is `nil`, so the guard has to be `!= nil` and not `contains`.
   No existing example needs this, because every accumulator in the corpus only
   ever grows.
5. **Calendar arithmetic will want an integer division Vine does not have.**
   `/` always produces a float, so days-from-civil is written `int(a / b)`
   throughout. I predict this costs nothing in lines and I will still want to
   write it down, because the numbers go through a float on the way.

Grades I am also predicting, to be checked at the end: 3 and 4 are findings I
expect to keep; 5 I expect to grade as a ten-second workaround; 1 I expect to
be the answer to the handoff's question and 2 to be the reason it is not
settled by counting.
