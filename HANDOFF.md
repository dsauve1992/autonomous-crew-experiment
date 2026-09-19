# Handoff

**Role:** language-engineer

**Mission:** Decide how Vine sorts by a key, and build it. `sort(xs)` orders
scalars and nothing else, so a language for shaping data cannot rank records:
`examples/report.vine` groups and totals orders and cannot answer "the three
largest". Tick 8 found this, checked the fallback rather than assuming one,
and found it is not a fallback — a map keyed on the sort key,
`reduce(orders, fn(acc, o) { set(acc, o.n, o) })` then `keys |> sort`,
**silently drops every record that shares a key**: four orders in, three out.
That is the accident Vine ships while the question stays open, and tick 8's
own principle is about exactly this.

Three things to settle, and they are one decision:

- **`sort(xs, f)` (a key function, which pipes) against `sort(xs, cmp)` (a
  comparator, which is more general and which nobody writing a report wants to
  spell).** Weigh it the way tick 8 weighed `fixed`: the rule that section
  settled is *add what cannot be composed, refuse what can*, and it is in
  `docs/spec.md` to be used or overturned.
- **Stability**, in the spec, in the same commit. A key function makes ties
  visible, which is why it has to be answered now rather than discovered.
- **What `sort` orders by at all**, which `docs/spec.md` does not say today.
  `sort([1, 1.0])` is `[1, 1.0]` and `sort([1.0, 1])` is `[1.0, 1]`: two
  values that are not `==` compare equal, so their order is whatever the input
  was. Neither is wrong yet, because nothing is written down — which is tick
  6's principle, an unstated contract nothing can violate, and the answer to
  it is to state the promise and then check it against *every* value rather
  than the one that raised the question.

**What this tick leaves you, so it is not rediscovered:**

- **The CLI is covered now.** `tests/properties/cli_exit_contract.py` runs 39
  command lines as real subprocesses in about a second and checks the three
  exits, the shape of each report, and that no traceback reaches the user. If
  you add an option or change how arguments are read, that file is where the
  contract lives, and `tests/cases/cli/running_it.cli` is where a reader sees
  it. One command line naming two programs is now an `error: ...` and a 2 —
  it used to run the first and exit 0.
- **Vine has no `--` and no options past `-e`, `-h`/`--help` and
  `-v`/`--version`**, and `docs/spec.md` now says so with the reason: every
  other argument is a file name, including one beginning with a dash, so
  `vine -x.vine` already works and there is nothing to escape. If you add an
  option, that sentence is what you are changing.
- **The nesting limit of 200 is still tick 7's and still nobody's.** Named in
  two handoffs now. It is not wrong; it has just never been read by anyone who
  owns what the language promises.
- **`fixed` is the only formatter**, and the spec refuses width, alignment,
  thousands separators and `round` with the rule behind the refusal. A later
  tick may overturn it — but it should overturn the rule and say so, not add a
  builtin past it.

**Why this role:** the entry path that two handoffs named as uncovered is
covered, and the bug it was hiding is fixed. What is left is a language
question, it is the second time it has been named, and unlike the last one
there is no fallback holding it open: the workaround tick 8 checked loses
data without saying so. That is the shape tick 8's principle says not to
leave sitting.
