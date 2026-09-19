"""The standard library. Every builtin receives (interp, pos, args)."""

import math
import re

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


def listing(names):
    """`int`, `int and string`, `int, string and nil`. For a message that has
    to name every kind it found rather than the first one it tripped on."""
    if len(names) < 2:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


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


# What `int` and `float` accept when handed a string, written out here rather
# than left to Python.
#
# Vine's lexer already decided what a number looks like, and said so: ASCII
# digits, because str.isdigit is Unicode-aware and would let `2²` lex as a
# number. `int(s)` is the other half of that question and had never been asked
# it, so it answered Python's way. `int("١٢٣")` was 123, and Unicode has 760
# decimal digits it read like that. `int("1_000")` was 1000 -- Python's
# spelling for a readable *literal*, honoured by a function that reads *data*,
# where `1_000` is a typo and not a thousand. And the space tolerated around
# the digits was Python's 29-character whitespace set, four of which are the
# ASCII information separators, rather than the four the lexer skips.
#
# So the alphabet is Vine's. The *shape* stays Python's: `".5"` and `"1."` are
# read, though neither is a literal a program may write. The lexer refuses
# those two because in a program `.` is also the member operator and `1.` may
# begin something longer; in a string there is nothing else for it to be, and
# a column of measurements contains `.5`.
SPACE = " \t\r\n"
INT_TEXT = re.compile(r"[+-]?[0-9]+")
FLOAT_TEXT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")

NUMBER_RULE = "the digits are 0 to 9, optionally signed, with spaces, tabs or newlines around them"
FINITE_RULE = "every float is finite; the largest is about 1.8e308"


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
        text = value.strip(SPACE)
        if INT_TEXT.fullmatch(text):
            return int(text)
        error = RuntimeError_(
            f"cannot convert {to_repr(value)} to an int", pos, interp.source
        )
        try:
            int(text)
        except ValueError:
            raise error  # not a number by anyone's reading
        # Python reads it and Vine does not, so every character in it is one
        # somebody meant as part of a number and the headline looks wrong.
        raise error.help(NUMBER_RULE)
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
        text = value.strip(SPACE)
        error = RuntimeError_(
            f"cannot convert {to_repr(value)} to a float", pos, interp.source
        )
        if FLOAT_TEXT.fullmatch(text):
            result = float(text)
            if result != result or result in (INFINITY, -INFINITY):
                # "1e400": the shape of a number, and past every float there
                # is. Same headline as text that is not a number at all,
                # because the answer is the same: no float here.
                raise error.help(FINITE_RULE)
            return result
        try:
            result = float(text)
        except ValueError:
            raise error  # not a number by anyone's reading
        if result != result or result in (INFINITY, -INFINITY):
            raise error.help(FINITE_RULE)  # "inf" and "nan", which Python reads
        raise error.help(NUMBER_RULE)  # a number, spelled a way Vine does not
    interp.fail(f"cannot convert {article(kind)} to a float", pos)


# -- numbers --------------------------------------------------------------

# The most digits `fixed` will write after the point. 1074 is not a round
# number and is not meant to be: the smallest float Vine has is 5e-324, which
# is exactly 2 ** -1074, and its decimal expansion ends at the 1074th place.
# So every float can be written out exactly, and every digit past the ceiling
# would be a zero. A ceiling is needed at all because Python's formatter
# refuses a precision above 2 ** 31 by raising, and below that quietly builds
# a string of that many characters.
MAX_DIGITS = 1074


@builtin("fixed", 2, 2)
def _fixed(interp, pos, args):
    value, digits = args
    kind = type_name(value)
    if kind not in ("int", "float"):
        interp.fail(f"fixed expects an int or float, got {kind}", pos)
    want(interp, pos, digits, "int", "fixed digits")
    if not 0 <= digits <= MAX_DIGITS:
        error = RuntimeError_(
            f"fixed digits must be between 0 and {MAX_DIGITS}, got {digits}",
            pos,
            interp.source,
        )
        if digits > MAX_DIGITS:
            error.help(
                f"the smallest float is 5e-324, which has {MAX_DIGITS} "
                "decimal places; nothing has more"
            )
        raise error
    point = "." + "0" * digits if digits else ""
    if kind == "int":
        # From the int's own digits, never through a float: an int may have
        # more digits than a float can hold, and Python's formatter converts
        # first -- so it raises on the ones that do not fit and rounds away
        # digits on the ones that only just do.
        return ("-" if value < 0 else "") + str(abs(value)) + point
    return format(value, f".{digits}f")



@builtin("pow", 2, 2)
def _pow(interp, pos, args):
    """`pow(x, y)` is x to the power y, and it is always a float.

    Always, because the alternative is a return type decided by the *value*
    of the exponent rather than its type: `pow(2, n)` would be an int for a
    positive whole n and a float for -1 or 0.5, and nothing else in Vine
    does that. `/` settled the same question the same way.

    It goes through math.pow rather than `**` for two reasons the tests
    below pin. `**` on ints is exact and unbounded, so `pow(10, 1000000000)`
    is an allocation rather than an answer -- no error, no result, a hang.
    And `**` returns a complex number for a negative base and a fractional
    exponent, which is not a Vine value and would reach the user as one.
    math.pow raises on both, and on overflow, where `**` hands back inf.
    """
    base, exponent = args
    for value, what in ((base, "pow base"), (exponent, "pow exponent")):
        kind = type_name(value)
        if kind not in ("int", "float"):
            interp.fail(f"{what} must be an int or float, got {kind}", pos)
        if kind == "int":
            try:
                float(value)
            except OverflowError:
                raise RuntimeError_(
                    "int is too large to convert to a float", pos, interp.source
                ).note("pow converts both of its arguments to a float") from None
    if base == 0 and exponent < 0:
        # 1 / 0, written the other way round. One fact, one headline -- and
        # the note, because nobody reading a line with no '/' in it goes
        # looking for a division.
        raise RuntimeError_("division by zero", pos, interp.source).note(
            "a negative power divides by the base, and the base is 0"
        )
    try:
        return math.pow(base, exponent)
    except ValueError:
        # The only domain error left: a negative base under a fractional
        # exponent. There is no real answer, and Vine has no other kind.
        raise RuntimeError_(
            "cannot raise a negative number to a fractional power", pos, interp.source
        ).note("the result would be a complex number") from None
    except OverflowError:
        interp.overflowed("pow", pos)

# -- lists ----------------------------------------------------------------


@builtin("range", 1, 2)
def _range(interp, pos, args):
    if len(args) == 1:
        start, stop = 0, want(interp, pos, args[0], "int", "range bound")
    else:
        start = want(interp, pos, args[0], "int", "range start")
        stop = want(interp, pos, args[1], "int", "range stop")
    try:
        return list(range(start, stop))
    except (OverflowError, MemoryError):
        # A list of that many elements cannot be built. Python says so two
        # ways -- OverflowError when the count will not fit the C integer a
        # length is, MemoryError when it fits and the memory does not -- and
        # they are one answer to the user, who asked for a list nothing can
        # hold. Neither was caught, so both arrived as Python tracebacks.
        interp.fail(f"range of {stop - start} elements is too large to build", pos)


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


def count(interp, pos, value, name):
    """The `n` of `take(xs, n)` and `drop(xs, n)`: an int, and not a negative
    one.

    A list shorter than `n` is not an error -- the list builtins are total,
    `first([])` is `nil` and `rest([])` is `[]`, and a report asking for its
    top three when it holds two rows wants two rows. A negative `n` is an
    error, because Vine already gives a negative integer a meaning against a
    list: `xs[-1]` is the last element. Answering `[]` would be answering a
    different question quietly.
    """
    want(interp, pos, value, "int", f"{name} count")
    if value < 0:
        raise RuntimeError_(
            f"{name} count must not be negative, got {value}", pos, interp.source
        ).help("a negative index counts from the end, but a count does not")
    return value


@builtin("take", 2, 2)
def _take(interp, pos, args):
    items = want(interp, pos, args[0], "list", "take target")
    return items[: count(interp, pos, args[1], "take")]


@builtin("drop", 2, 2)
def _drop(interp, pos, args):
    items = want(interp, pos, args[0], "list", "drop target")
    return items[count(interp, pos, args[1], "drop") :]


@builtin("reverse", 1, 1)
def _reverse(interp, pos, args):
    value = args[0]
    if type_name(value) == "list":
        return list(reversed(value))
    if type_name(value) == "string":
        return value[::-1]
    interp.fail(f"reverse expects a list or string, got {type_name(value)}", pos)


def unorderable(values):
    """The type names in `values`, in the order they first appear, if they
    cannot all be ordered against each other -- otherwise None.

    `sort` orders by `<`, and `<` relates numbers with numbers and strings
    with strings, so sort's reach is exactly `<`'s and no wider. An empty list
    has nothing to order and is fine.
    """
    kinds = []
    for value in values:
        kind = type_name(value)
        if kind not in kinds:
            kinds.append(kind)
    if set(kinds) <= {"int", "float"} or kinds in ([], ["string"]):
        return None
    return kinds


@builtin("sort", 1, 2)
def _sort(interp, pos, args):
    items = want(interp, pos, args[0], "list", "sort argument")
    if len(args) == 1:
        kinds = unorderable(items)
        if kinds:
            interp.fail(
                "sort expects a list of numbers or a list of strings, got a "
                f"list holding {listing(kinds)}",
                pos,
            )
        return sorted(items)
    fn = want_callable(interp, pos, args[1], "sort key function")
    # Every key first, in list order, and then one comparison-free pass over
    # them: a key function is ordinary Vine and may print, so when it runs has
    # to be a promise rather than whatever the sort algorithm happens to do.
    keys = [interp.call(fn, [item], pos) for item in items]
    kinds = unorderable(keys)
    if kinds:
        interp.fail(
            f"sort keys must be all numbers or all strings, got {listing(kinds)}",
            pos,
        )
    # Sorting the positions rather than the items is what makes the sort
    # stable without asking Python's sort to compare two records: equal keys
    # leave in the order their positions did, which is the order they arrived.
    return [items[i] for i in sorted(range(len(items)), key=lambda i: keys[i])]


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
    for i, item in enumerate(items):
        # The index is the only "where" there is. The caret is on the call,
        # and a list built by a pipeline has no source position per element
        # to move it to even if moving it were allowed.
        want(interp, pos, item, "string", f"join element at index {i}")
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
