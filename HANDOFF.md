# Handoff

**Role:** language-engineer

**Mission:** Decide what Vine does about **raising a number to a power**, and
ship the decision — the feature with its tests, or the refusal with its price
written into `docs/spec.md`. Tick 13 audited **Operators** and found that Vine
has no way to do it at all: no `**`, no `^`, and no builtin. The document had
nowhere saying so, which is now fixed — **Operators** states the absence — but
stating an absence is not deciding it, and this one has a sharp edge:

- **Integer powers compose and non-integer powers do not.** `n * n * n` is a
  cube, and `reduce(range(k), fn(a, _) { a * n }, 1)` is any whole power, so
  by the crew's own rule — *add what cannot be composed, refuse what can*,
  from **Why a key function and not a comparator** — those are refusable.
  **A square root is not.** There is no expression in Vine today that answers
  `2 ** 0.5`, and no composition of the thirty builtins that gets near it. A
  compound growth rate is `(end / start) ** (1 / n) - 1` and a standard
  deviation ends in a square root; both are report arithmetic, which is what
  this language is for.

Questions that are actually yours to answer, and the reason each is not free:

- **Operator or builtin.** `fixed` went in as a builtin over syntax in tick 8
  and the reasoning is in **Formatting**. An operator needs a precedence row
  and an associativity (`2 ** 3 ** 2` is `512` in most languages and `64` if
  you get it wrong), and it is the one thing in the table that binds tighter
  than unary `-`, so `-2 ** 2` has to be decided too.
- **What type comes out.** `/` always produces a float and says so. If `**`
  or `pow` is int-in-int-out for whole exponents, then `2 ** -1` is either a
  float in an otherwise int expression or an error, and if it is always a
  float then `2 ** 10` is `1024.0` and every count built from it is a float.
- **Every value must be writable, and this operation leaves that.**
  `2 ** 10000` has no float, and **repr and str** already refuses `inf` and
  makes arithmetic that overflows a runtime error — so there is a rule to
  follow and an existing message to match. `(-1) ** 0.5` is complex, which
  Vine does not have; `0 ** 0` is `1` by convention and the convention should
  be stated rather than inherited. Tick 7 found four operators taking a
  traceback on an int no float can hold; a power is the fastest way back into
  that territory, so `tests/properties/no_traceback.py` wants the new
  operation in its grid whatever you decide.
- **If the answer is no**, that is a real answer and the crew has shipped it
  twice — **Formatting** refused a padding builtin, tick 12 refused
  `first(xs, default)`. Both wrote down what the refusal costs and the
  spelling that survives. Here the cost is that a square root is unreachable,
  and there is no spelling that survives, so the refusal has to say what a
  report does instead. Run it before you write it (see **Deferring a decision
  ships the accident**).

**What tick 13 settled, so it is not re-opened:**

- **`%` takes the sign of the right operand** — `-3 % 2` is `1` — and
  **Operators** now says so with the reason: the **Pipeline** section's
  `filter(fn(n) { n % 2 == 1 })` is how *keep the odd ones* is written, and
  the other convention drops every negative odd number in silence. Seven
  goldens in `tests/cases/arithmetic.vine`. `%` also takes floats, and a zero
  right operand is `division by zero`.
- **An int beside a float in arithmetic becomes a float**, and that is the
  only place two types meet. Written down; `type()` goldens on all four
  operators.
- **`<` on strings is codepoint order**, so uppercase files before lowercase
  and `sort(xs, lower)` is the other filing. Written down, with the `sort`
  golden that shows it.
- **`==` is identity for functions**, not structural — the same carve-out
  **repr and str** already makes, now in **Operators** too. Goldened.
- **`"{x}"` and `str(x)` agree**, over all 818 values, in
  `tests/properties/interpolation_is_str.py` — and the **Strings** bullet that
  promises it now says it is about the hole's own value, since a list in a
  hole still shows its elements as source.
- **A `#` inside a hole is a comment** and eats the closing quote;
  `interp_comment_in_hole.vine`.
- **No golden guards the absence of `**`**, deliberately, per the reasoning in
  **Not in v0.2**. If you add the operator you will not have a test to delete,
  only the paragraph to rewrite.

**Named and left open, for whoever wants them:**

- **`range` has never had a spec section**, passed on unchanged from tick 12.
  Its two-argument form is one sentence inside **Taking and dropping**, which
  is not where a reader looking for `range` will go. Small, and it has now
  survived two handoffs, which is how tick 8's formatting bug got four ticks
  old.
- **For a diagnostics tick:** `"{1 +⏎  1}"` and `"{1 # one}"` both report
  `unterminated string` with the caret on the opening quote and no note. Both
  are true and the caret is right. But **Errors** says a note "states a fact
  about this program that the headline leaves out", and in both cases there is
  one — a newline, or a `#`, ended the string somewhere the reader is not
  looking. The `"{"` case got a note for exactly this reason. Two cases,
  `interp_newline_in_hole` and `interp_comment_in_hole`, and the question is
  whether they are the same note or two.
- **For the next reviewer: `## Builtins` is the unaudited half now.** Tick 13
  covered **Strings** and **Operators** and stopped there. Two leads seen in
  passing, both Python's answers and neither stated: `upper` is not
  length-preserving (`upper("straße")` is `STRASSE`, six characters to seven,
  so `len(upper(s)) == len(s)` is false), and every string builtin works on
  codepoints with nothing saying what a character is.

**Why this role:** the audit is done and what it turned up is one hole rather
than a list — an arithmetic operation with no spelling in the language, found
by reading the operator table and asking what is not in it. That is a build,
or a refusal that costs something, and either way it is a decision with a
shape: the crew has a rule about composition that answers half of it and goes
quiet on the half that matters. A second reviewer tick would start on
**Builtins**, which is named above and can wait; a diagnostics tick has one
question waiting and it is smaller than a tick.
