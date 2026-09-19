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


def to_key(v):
    """The internal identity of a map key.

    Vine's equality is type-strict: `1`, `1.0` and `true` are three different
    values. Python's is not -- all three are equal to each other and hash
    alike -- so a dict keyed on them directly collapses the three into one
    entry, and `{1: "a", true: "b"}` would answer `{1: "b"}`. Keys are stored
    tagged with their type name, and untagged on the way back out.
    """
    return (type_name(v), v)


def from_key(k):
    return k[1]


def to_repr(v):
    """Vine source for a value -- see `repr and str` in docs/spec.md.

    Every escape here exists to keep `repr` output readable back in. `{` is on
    the list because interpolation made it structural: without it `repr("\\{")`
    answers `"{"`, which is a string nothing can type. `}` is not, because a
    lone `}` outside a hole is already literal.
    """
    if isinstance(v, str):
        body = (
            v.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("{", "\\{")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
        )
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
