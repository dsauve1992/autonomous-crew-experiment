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
- **replace.** **Text** refuses a `replace` builtin on the ground that
  `join(split(s, from), to)` already is one. The other three clauses compare
  two Vine spellings, because each of those sentences is an equality between
  two of them. This one cannot: the thing the composition is claimed to equal
  is not in Vine and never will be, so the right-hand side is written below as
  a scan -- find the needle, emit the prefix and the replacement, advance past
  it -- and the clause checks the composition against a *definition* rather
  than against another run. It is also the one clause with a stated exception,
  an empty `from`, so it checks that too rather than skipping it: the
  exception being exactly one case is the part of the refusal that could rot.
"""

import io

from vine import run
from vine.errors import VineError

CLAIM = (
    "print's separator, push, concat and the split/join spelling of replace each "
    "answer exactly what docs/spec.md says they are the same as"
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

# The replace clause needs strings rather than values, and the characters that
# matter are a separator that occurs twice running, one that never occurs, and
# one no program can type. RS is pasted into the Vine source this file builds;
# it is spelled chr(0x1E) here so a reader of *this* file can see it.
RS = chr(0x1E)
TEXT_ALPHABET = ["a", ",", RS]
TEXTS = [""]
for _n in (1, 2, 3):
    _prev = [t for t in TEXTS if len(t) == _n - 1]
    TEXTS += [t + c for t in _prev for c in TEXT_ALPHABET]
# An empty needle is the stated exception, not an omission, so it is in here.
NEEDLES = ["a", ",", RS, "a,", ",,", ""]
REPLACEMENTS = ["", "x", ",,", RS]


def as_source(s):
    """`s` as a Vine string literal. Only `"` and `\\` need escaping, and the
    invisible characters need none -- being unable to write them is the point
    of the paragraph this clause guards."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def scan_replace(s, needle, to):
    """A left-to-right, non-overlapping replace, defined rather than borrowed.

    This is the sentence `join(split(s, from), to)` is claimed to mean. It does
    not call split, join or str.replace, so a shared bug has nowhere to hide.
    """
    out = []
    i = 0
    while True:
        hit = s.find(needle, i)
        if hit < 0:
            break
        out.append(s[i:hit])
        out.append(to)
        i = hit + len(needle)
    out.append(s[i:])
    return "".join(out)


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

    # replace(s, from, to) is join(split(s, from), to) -- Text. For a non-empty
    # `from` the two are the same function; for an empty one they part, and
    # that is the stated exception rather than a hole, so it is pinned to the
    # only other thing it could be: `to` between the codepoints of `s`, which
    # is what **split and join are a pair** already promises split does.
    for s in TEXTS:
        for needle in NEEDLES:
            for to in REPLACEMENTS:
                checked += 1
                call = (
                    f"print(repr(join(split({as_source(s)}, {as_source(needle)}), "
                    f"{as_source(to)})))"
                )
                composed = answer(call)
                if needle == "":
                    expected = to.join(list(s))
                else:
                    expected = scan_replace(s, needle, to)
                wanted = answer(f"print(repr({as_source(expected)}))")
                if composed != wanted:
                    failures.append(
                        (
                            f"join(split({s!r}, {needle!r}), {to!r})",
                            f"answered {composed!r}; a scan says {wanted!r}",
                        )
                    )

    return checked, failures
