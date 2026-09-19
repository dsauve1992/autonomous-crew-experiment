"""Every composition `docs/spec.md` offers in place of a builtin answers what
the builtin answers.

Three sections now refuse, keep or explain a builtin by saying what it is the
same as. **Printing** says the separator is a convenience because `print(a, b)`
is `print(join(map([a, b], str), " "))`. **Building lists** keeps `push` and
`concat` against the rule *add what cannot be composed, refuse what can*, and
both halves of that argument are equalities: `push(xs, x)` is
`concat(xs, [x])` exactly, and `concat(a, b)` is `a + b` on lists and nothing
like it anywhere else.

Tick 14's principle is that "X composes out of Y" is a statement about
equality over a domain, and sampling the domain is systematically misleading.
It was learned by enumerating one such claim once, by hand, in a scratch file
that was thrown away -- and the number it produced went into the spec guarded
by nothing. These three are enumerated here instead, so the sentences stay
true as `VALUES` grows rather than as of the afternoon somebody typed them.

Which half of each clause is real, because a check that compares two things
the document treats as separate can be comparing one thing (tick 13):

- **print.** Both sides reach `to_display` for each element, so the
  conversion is shared and this clause cannot test it. What it tests is the
  joining: `" ".join(...)` inside `_print` against `_join`'s loop over a list
  `map` built. Those are three separate functions and one of them type-checks
  its elements. It runs at four arities because the promise is about any
  number of arguments and two is the arity at which a separator bug is
  smallest -- zero arguments and one have no separator at all to get wrong,
  which is the half a pair cannot check.
- **push.** `_push` and `_concat` both end in a Python `+`, and that much is
  shared. The composition is not: the right-hand side has a one-element list
  *literal* in it, which is evaluated by the interpreter and written nowhere
  in `builtins.py`. Wrapping and unwrapping is the step being checked.
- **concat.** `_concat` and the `+` branch of `eval_binary` are two sites,
  and the half that is not a shared primitive is the disagreement: `concat`
  refuses every pair `+` accepts that is not two lists. The claim is not that
  they agree, it is *where* they agree, so both directions are checked.
"""

import io

from vine import run
from vine.errors import VineError

CLAIM = (
    "print's separator, push and concat each answer exactly what docs/spec.md "
    "says they are the same as, over every value the grid holds"
)

from no_traceback import VALUES

LISTS = [v for v in VALUES if v.startswith("[")]

# print's contract is about any number of arguments, so the clause has to be
# about more than two. Arities 0 and 1 run over all of VALUES; arity 3 runs
# over every triple of the six below rather than every triple of VALUES,
# which would be 29791 programs for a claim the pairs have already made. A
# subset enumerated whole is still an enumeration -- what this file must not
# do is pick pairs at random, because a counterexample has to come back on
# the next ./check.
TRIPLES = ['1', '"s"', "nil", "[1]", "{a: 1}", "fn(x) { x }"]


def answer(src):
    """What a one-line program writes, or the Vine error it fails with.

    A Vine error is an answer here: two spellings that fail identically are
    two spellings of the same thing, which is what the equalities claim.
    """
    out = io.StringIO()
    try:
        run(src, "<composition>", out)
    except VineError as e:
        return "error: " + str(e)
    return out.getvalue()


def check():
    checked = 0
    failures = []

    # print(...) is print(join(map([...], str), " ")) -- Printing. At every
    # arity, including none: print() and print(join(map([], str), " ")) are
    # both a blank line, which is the one place the empty list has to carry
    # the claim.
    argument_lists = (
        [[]]
        + [[a] for a in VALUES]
        + [[a, b] for a in VALUES for b in VALUES]
        + [[a, b, c] for a in TRIPLES for b in TRIPLES for c in TRIPLES]
    )
    for args in argument_lists:
        checked += 1
        written = ", ".join(args)
        direct = answer(f"print({written})")
        composed = answer(f'print(join(map([{written}], str), " "))')
        if direct != composed:
            failures.append(
                (
                    f"print({written})",
                    f"wrote {direct!r}; the join spelling wrote {composed!r}",
                )
            )

    # push(xs, x) is concat(xs, [x]) -- Building lists.
    for xs in LISTS:
        for x in VALUES:
            checked += 1
            direct = answer(f"print(repr(push({xs}, {x})))")
            composed = answer(f"print(repr(concat({xs}, [{x}])))")
            if direct != composed:
                failures.append(
                    (
                        f"push({xs}, {x})",
                        f"answered {direct!r}; concat({xs}, [{x}]) answered {composed!r}",
                    )
                )

    # concat(a, b) is a + b on two lists, and on nothing else -- Building
    # lists. Where they agree is the claim, so a pair that is not two lists
    # and does not make concat fail breaks it just as a disagreeing pair of
    # lists does.
    for a in VALUES:
        for b in VALUES:
            checked += 1
            direct = answer(f"print(repr(concat({a}, {b})))")
            operator = answer(f"print(repr({a} + {b}))")
            both_lists = a in LISTS and b in LISTS
            if both_lists and direct != operator:
                failures.append(
                    (
                        f"concat({a}, {b})",
                        f"answered {direct!r}; {a} + {b} answered {operator!r}",
                    )
                )
            if not both_lists and not direct.startswith("error: "):
                failures.append(
                    (
                        f"concat({a}, {b})",
                        f"answered {direct!r} for a pair that is not two lists",
                    )
                )

    return checked, failures
