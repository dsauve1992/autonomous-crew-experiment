"""Runtime values: how they are represented, named, printed and compared."""

# Vine has no infinities and no nan -- see `repr and str` in docs/spec.md.
# This exists so the three guards that keep them out can say so by name.
INFINITY = float("inf")


class Function:
    """A closure: parameters, body, and the environment it was created in.

    `pos` is where its `fn` was written. A closure is called from somewhere
    else -- in the REPL, from an entry typed long after it -- so an arity
    error has two places worth naming and the caret can only be at one.
    """

    def __init__(self, params, body, env, name=None, pos=None):
        self.params = params
        self.body = body
        self.env = env
        self.name = name
        self.pos = pos

    @property
    def label(self):
        return self.name or "<anonymous>"


class Builtin:
    """A function implemented in Python. `fn` receives (interp, pos, args)."""

    def __init__(self, name, fn, arity):
        self.name = name
        self.fn = fn
        self.arity = arity  # (min, max); max None means variadic


def type_name(v):
    if v is None:
        return "nil"
    if v is True or v is False:
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "map"
    if isinstance(v, (Function, Builtin)):
        return "function"
    return "unknown"


def is_truthy(v):
    """Only nil and false are falsy. 0 and "" are true."""
    return not (v is None or v is False)


def equal(a, b):
    """Structural equality. Types must match; 1 and 1.0 are not equal."""
    if type_name(a) != type_name(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        if len(a) != len(b):
            return False
        return all(k in b and equal(v, b[k]) for k, v in a.items())
    if isinstance(a, (Function, Builtin)):
        return a is b
    return a == b


def holds_function(v):
    """Whether `v` is a function or has one somewhere inside it.

    The one thing a map key may not be -- see `Composite keys` in
    docs/spec.md. Every other value is allowed, because key identity is `==`
    and `equal` decides `==` for every other value structurally. It decides
    it for a function with `is`, so two closures that read alike are two
    keys, and a key nothing can write down twice is a key that can only miss.
    """
    if isinstance(v, (Function, Builtin)):
        return True
    if isinstance(v, list):
        return any(holds_function(x) for x in v)
    if isinstance(v, dict):
        # A key already passed this test on its way in, so only the values
        # can be carrying one.
        return any(holds_function(x) for x in v.values())
    return False


def function_path(v, path=""):
    """Where the function inside `v` is, written as Vine indexing.

    `[trim]` answers `[0]` and `{a: [trim]}` answers `["a"][0]`. A note can
    say this and the caret cannot: the key is one expression, and the part of
    it that is wrong may be six fields down a record written somewhere else.
    """
    if isinstance(v, (Function, Builtin)):
        return path
    if isinstance(v, list):
        for i, x in enumerate(v):
            if holds_function(x):
                return function_path(x, f"{path}[{i}]")
    if isinstance(v, dict):
        for k, x in v.items():
            if holds_function(x):
                return function_path(x, f"{path}[{to_repr(from_key(k))}]")
    return path  # pragma: no cover - only called where one was found


def canonical(v):
    """A hashable form of `v` in which two values are equal exactly when
    `equal(v, w)` says they are.

    Vine's equality is type-strict: `1`, `1.0` and `true` are three different
    values. Python's is not -- all three are equal to each other and hash
    alike -- so a dict keyed on them directly collapses the three into one
    entry, and `{1: "a", true: "b"}` would answer `{1: "b"}`. Hence the type
    tag, at every depth.

    A list becomes a tuple of its elements' canonical forms, in order, since
    `equal` compares lists element for element. A map becomes a *frozenset*
    of its pairs, because `equal` does not compare a map's order and
    **Map order** says so by name: `{a: 1, b: 2}` and `{b: 2, a: 1}` are one
    key, and an order-sensitive form would make them two.

    This and `equal` are two statements of one rule, so they can disagree --
    and a disagreement is a map that answers the wrong value rather than an
    error. `tests/properties/key_identity_is_equality.py` is what holds them
    to each other.
    """
    if isinstance(v, list):
        return ("list", tuple(canonical(x) for x in v))
    if isinstance(v, dict):
        return ("map", frozenset((k.canon, canonical(x)) for k, x in v.items()))
    return (type_name(v), v)


class Key:
    """A map key's slot in the dict underneath: its identity, and itself.

    The identity is `canonical(value)`, which is what the dict hashes and
    compares. The value is kept beside it so `keys(m)` can hand back the list
    or the map that was offered, in its own order, rather than a rebuilt one
    -- a frozenset has no order to rebuild from.

    Which of two `==` keys is kept is then decided by Python's dict, which
    keeps the key it already had: `set(m, k, v)` on a key the map has keeps
    that key's place *and* its spelling. That is **Map order**'s rule one
    level down, and it is the same answer for the same reason.
    """

    __slots__ = ("value", "canon", "_hash")

    def __init__(self, value):
        self.value = value
        self.canon = canonical(value)
        self._hash = hash(self.canon)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, Key):
            return NotImplemented
        return self.canon == other.canon

    def __repr__(self):  # pragma: no cover - for a Python debugger only
        return f"Key({self.value!r})"


def to_key(v):
    """The internal identity of a map key. See `Key`."""
    return Key(v)


def from_key(k):
    return k.value


# What `repr` writes in place of a character, and everything not in here is
# written as itself. The named escapes first, then every C0 and C1 control as
# a codepoint escape -- `chr(0)` through `chr(0x1f)`, and `chr(0x7f)` through
# `chr(0x9f)` -- except the three that already have a shorter spelling.
#
# That range and no wider, and the reason is the one **Text** gives for `len`
# counting codepoints: an answer that needs a Unicode table is an answer that
# changes with the table. Asking `unicodedata` which characters are invisible
# would escape the non-breaking space too, and would also make `repr(s)` --
# a value a Vine program can compare and print -- depend on which Unicode
# release Python was built against. The controls are the largest set the
# standard has closed forever, so this answer is the same on every machine.
REPR_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "{": "\\{",
    "\n": "\\n",
    "\t": "\\t",
    "\r": "\\r",
}
REPR_ESCAPES.update(
    {
        chr(c): f"\\u{{{c:x}}}"
        for c in list(range(0x00, 0x20)) + list(range(0x7F, 0xA0))
        if chr(c) not in REPR_ESCAPES
    }
)


# The last codepoint `reveal` leaves alone. Everything above it is written as
# a codepoint escape, on top of every escape `repr` already makes -- so
# `reveal` output holds nothing but U+0020 through U+007E.
#
# `repr` refused a wider set because the wide notions of *invisible* are
# Unicode categories, and a category is a table that moves between releases;
# `repr(s)` is a value a program stores and compares, so it may not move. This
# boundary is not a category. Printable ASCII is frozen and was frozen before
# Unicode existed, so `reveal` can be wider than `repr` without taking on the
# thing `repr` refused. See `Revealing` in docs/spec.md.
REVEAL_CEILING = 0x7E


def to_reveal(s):
    """Vine source for a string in which every character can be seen.

    `repr` plus one rule: a codepoint above `REVEAL_CEILING` is written as an
    escape too. `repr` already escapes everything below U+0020 and U+007F
    through U+009F, so what is left as itself is exactly printable ASCII.

    The quotes are part of it and not decoration. A trailing space is as
    invisible as a zero-width one, and no escape set that keeps ASCII
    printable can show it; the closing quote is what shows it.
    """
    body = "".join(
        REPR_ESCAPES.get(ch, ch) if ord(ch) <= REVEAL_CEILING else f"\\u{{{ord(ch):x}}}"
        for ch in s
    )
    return f'"{body}"'


def to_repr(v):
    """Vine source for a value -- see `repr and str` in docs/spec.md.

    Every escape here exists to keep `repr` output readable back in. `{` is on
    the list because interpolation made it structural: without it `repr("\\{")`
    answers `"{"`, which is a string nothing can type. `}` is not, because a
    lone `}` outside a hole is already literal. The controls are on it so the
    output is readable at all, which is a separate promise -- see
    REPR_ESCAPES above, and `repr_is_legible.py` under tests/properties.

    One pass over the characters rather than a chain of replaces. The chain
    was correct only because the backslash was replaced first; a codepoint
    escape adds a second constraint from the other end, since the backslash
    it writes must not then be escaped again. Two ordering constraints on six
    lines that do not state them is a bug waiting for the next escape.
    """
    if isinstance(v, str):
        body = "".join(REPR_ESCAPES.get(ch, ch) for ch in v)
        return f'"{body}"'
    return to_display(v)


def to_display(v):
    """How a value looks when printed on its own."""
    if v is None:
        return "nil"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, float):
        if v != v:
            return "nan"
        if v in (float("inf"), float("-inf")):
            return "inf" if v > 0 else "-inf"
        return repr(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "[" + ", ".join(to_repr(x) for x in v) + "]"
    if isinstance(v, dict):
        return (
            "{"
            + ", ".join(f"{to_repr(from_key(k))}: {to_repr(x)}" for k, x in v.items())
            + "}"
        )
    if isinstance(v, Function):
        return f"<fn {v.label}/{len(v.params)}>"
    if isinstance(v, Builtin):
        return f"<builtin {v.name}>"
    return str(v)
