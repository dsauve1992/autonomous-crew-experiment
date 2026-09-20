# Examples

Every `.vine` file here has a `.out` file beside it and is run by `./check`, so
an example that stops working fails the build. Add examples freely; add the
expected output by hand at the same time.

Two of them are not programs to read but **modules** the others import:
`table.vine` (`pad`, `rjust`, `widest`) and `dates.vine` (`slice`,
`all_digits`, `is_date`). Their goldens are empty, and that is the check — a
module's top-level statements run when it is first imported, so one that
printed would print in the middle of whatever report was using it.
