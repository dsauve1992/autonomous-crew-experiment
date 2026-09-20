# Examples

Every `.vine` file here has a `.out` file beside it and is run by `./check`, so
an example that stops working fails the build. Add examples freely; add the
expected output by hand at the same time.

Three of them are not programs to read but **modules** the others import:
`table.vine` (columns), `dates.vine` (a date out of a field) and `clock.vine`
(timestamps, which imports `dates.vine` in turn). Their goldens are empty, and
that is the check — a module's top-level statements run when it is first
imported, so one that printed would print in the middle of whatever report was
using it.

Two of the programs are handed a file rather than carrying one:

    vine examples/statement.vine < examples/statement.in
    vine examples/pipeline.vine < examples/pipeline.in
