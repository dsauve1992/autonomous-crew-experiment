"""The standard library. Every builtin receives (interp, pos, args)."""

from .errors import RuntimeError_
from .values import (
    INFINITY,
    Builtin,
    Function,
    from_key,
    to_display,
    to_repr,
    type_name,
)

REGISTRY = []


def builtin(name, low, high):
    """Register a builtin taking between `low` and `high` arguments."""

    def wrap(fn):
        REGISTRY.append(Builtin(name, fn, (low, high)))
        return fn

    return wrap


def install(env):
    for b in REGISTRY:
        env.define(b.name, b)


def article(kind):
    """`a list`, `an int`. Gluing "a " to a type name says "a int" one time in
    three, and no case had ever printed one of those three."""
    return f"an {kind}" if kind[0] in "aeiou" else f"a {kind}"


def want(interp, pos, value, kind, what):
    if type_name(value) != kind:
        interp.fail(f"{what} must be {article(kind)}, got {type_name(value)}", pos)
    return value


def want_callable(interp, pos, value, what):
    if not isinstance(value, (Function, Builtin)):
        interp.fail(f"{what} must be a function, got {type_name(value)}", pos)
    return value


# -- output ---------------------------------------------------------------


@builtin("print", 0, None)
def _print(interp, pos, args):
    interp.out.write(" ".join(to_display(a) for a in args) + "\n")
    return None


@builtin("repr", 1, 1)
def _repr(interp, pos, args):
    return to_repr(args[0])


# -- general --------------------------------------------------------------


@builtin("type", 1, 1)
def _type(interp, pos, args):
    return type_name(args[0])


@builtin("len", 1, 1)
def _len(interp, pos, args):
    value = args[0]
    if type_name(value) in ("string", "list", "map"):
        return len(value)
    interp.fail(f"len expects a string, list or map, got {type_name(value)}", pos)


@builtin("str", 1, 1)
def _str(interp, pos, args):
    return to_display(args[0])


@builtin("int", 1, 1)
def _int(interp, pos, args):
    value = args[0]
    kind = type_name(value)
    if kind == "int":
        return value
    if kind == "float":
        # Every Vine float is finite, so every one of them has an int. The
        # guard that used to stand here was tick 3's, against nan and inf
        # reaching Python's int() and raising; those two stopped being values
        # in tick 6, and the fence moved to where they were born.
        return int(value)
    if kind == "bool":
        return 1 if value else 0
    if kind == "string":
        try:
            return int(value.strip())
        except ValueError:
            interp.fail(f"cannot convert {to_repr(value)} to an int", pos)
    interp.fail(f"cannot convert {article(kind)} to an int", pos)


@builtin("float", 1, 1)
def _float(interp, pos, args):
    value = args[0]
    kind = type_name(value)
    if kind in ("int", "float"):
        try:
            return float(value)
        except OverflowError:  # an int with more digits than a float can hold
            interp.fail("int is too large to convert to a float", pos)
    if kind == "string":
        try:
            result = float(value.strip())
        except ValueError:
            interp.fail(f"cannot convert {to_repr(value)} to a float", pos)
        if result != result or result in (INFINITY, -INFINITY):
            # "inf", "nan" and "1e400" all parse in Python, and none of the
            # three is a Vine value. Same headline as a string that is not a
            # number at all, because the answer is the same: no float here.
            raise RuntimeError_(
                f"cannot convert {to_repr(value)} to a float", pos, interp.source
            ).help("every float is finite; the largest is about 1.8e308")
        return result
    interp.fail(f"cannot convert {article(kind)} to a float", pos)


# -- lists ----------------------------------------------------------------


@builtin("range", 1, 2)
def _range(interp, pos, args):
    if len(args) == 1:
        start, stop = 0, want(interp, pos, args[0], "int", "range bound")
    else:
        start = want(interp, pos, args[0], "int", "range start")
        stop = want(interp, pos, args[1], "int", "range stop")
    return list(range(start, stop))


@builtin("map", 2, 2)
def _map(interp, pos, args):
    items = want(interp, pos, args[0], "list", "map target")
    fn = want_callable(interp, pos, args[1], "map function")
    return [interp.call(fn, [item], pos) for item in items]


@builtin("filter", 2, 2)
def _filter(interp, pos, args):
    from .values import is_truthy

    items = want(interp, pos, args[0], "list", "filter target")
    fn = want_callable(interp, pos, args[1], "filter predicate")
    return [item for item in items if is_truthy(interp.call(fn, [item], pos))]


@builtin("reduce", 3, 3)
def _reduce(interp, pos, args):
    items = want(interp, pos, args[0], "list", "reduce target")
    fn = want_callable(interp, pos, args[1], "reduce function")
    acc = args[2]
    for item in items:
        acc = interp.call(fn, [acc, item], pos)
    return acc


@builtin("push", 2, 2)
def _push(interp, pos, args):
    items = want(interp, pos, args[0], "list", "push target")
    return items + [args[1]]


@builtin("concat", 2, 2)
def _concat(interp, pos, args):
    a = want(interp, pos, args[0], "list", "concat argument")
    b = want(interp, pos, args[1], "list", "concat argument")
    return a + b


@builtin("first", 1, 1)
def _first(interp, pos, args):
    items = want(interp, pos, args[0], "list", "first argument")
    return items[0] if items else None


@builtin("rest", 1, 1)
def _rest(interp, pos, args):
    items = want(interp, pos, args[0], "list", "rest argument")
    return items[1:]


@builtin("reverse", 1, 1)
def _reverse(interp, pos, args):
    value = args[0]
    if type_name(value) == "list":
        return list(reversed(value))
    if type_name(value) == "string":
        return value[::-1]
    interp.fail(f"reverse expects a list or string, got {type_name(value)}", pos)


@builtin("sort", 1, 1)
def _sort(interp, pos, args):
    items = want(interp, pos, args[0], "list", "sort argument")
    kinds = {type_name(x) for x in items}
    if kinds <= {"int", "float"} or kinds <= {"string"} or not kinds:
        return sorted(items)
    interp.fail("sort expects a list of numbers or a list of strings", pos)


@builtin("contains", 2, 2)
def _contains(interp, pos, args):
    from .values import equal

    target, needle = args
    kind = type_name(target)
    if kind == "list":
        return any(equal(x, needle) for x in target)
    if kind == "map":
        # A needle that cannot be a key gets the same answer the string branch
        # gives a needle that is not a string: an error, not `false`. Asking
        # whether a list is a key is a category mistake, not a lookup that
        # missed -- absence is what `get(m, k, default)` is for.
        return interp.key_for(needle, pos) in target
    if kind == "string":
        return want(interp, pos, needle, "string", "contains needle") in target
    interp.fail(f"contains expects a list, map or string, got {kind}", pos)


# -- maps -----------------------------------------------------------------


@builtin("keys", 1, 1)
def _keys(interp, pos, args):
    target = want(interp, pos, args[0], "map", "keys argument")
    return [from_key(k) for k in target]


@builtin("values", 1, 1)
def _values(interp, pos, args):
    return list(want(interp, pos, args[0], "map", "values argument").values())


@builtin("get", 2, 3)
def _get(interp, pos, args):
    target = want(interp, pos, args[0], "map", "get target")
    default = args[2] if len(args) == 3 else None
    return target.get(interp.key_for(args[1], pos), default)


@builtin("set", 3, 3)
def _set(interp, pos, args):
    target = want(interp, pos, args[0], "map", "set target")
    out = dict(target)
    out[interp.key_for(args[1], pos)] = args[2]
    return out


# -- strings --------------------------------------------------------------


@builtin("split", 2, 2)
def _split(interp, pos, args):
    text = want(interp, pos, args[0], "string", "split target")
    sep = want(interp, pos, args[1], "string", "split separator")
    return list(text) if sep == "" else text.split(sep)


@builtin("join", 2, 2)
def _join(interp, pos, args):
    items = want(interp, pos, args[0], "list", "join target")
    sep = want(interp, pos, args[1], "string", "join separator")
    for item in items:
        want(interp, pos, item, "string", "join element")
    return sep.join(items)


@builtin("upper", 1, 1)
def _upper(interp, pos, args):
    return want(interp, pos, args[0], "string", "upper argument").upper()


@builtin("lower", 1, 1)
def _lower(interp, pos, args):
    return want(interp, pos, args[0], "string", "lower argument").lower()


@builtin("trim", 1, 1)
def _trim(interp, pos, args):
    return want(interp, pos, args[0], "string", "trim argument").strip()
