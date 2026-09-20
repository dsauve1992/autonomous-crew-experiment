"""The tree-walking evaluator."""

import contextlib
import sys

from .errors import Pos, RuntimeError_
from .nodes import (
    Binary,
    Block,
    Call,
    FnLit,
    Ident,
    If,
    Index,
    Let,
    ListLit,
    Literal,
    Logical,
    MapLit,
    Return,
    StrLit,
    Unary,
)
from .rules import (
    CALL_DEPTH_RULE,
    FLOAT_CEILING,
    KEY_RULE,
    MAX_DEPTH,
    MAX_VALUE_DEPTH,
    SET_RULE,
    VALUE_DEPTH_RULE,
)
from .values import (
    Builtin,
    Function,
    INFINITY,
    TooDeep,
    equal,
    function_path,
    holds_function,
    is_truthy,
    to_display,
    to_key,
    to_repr,
    type_name,
)

# One Vine call costs several Python frames, so CPython's own limit would fire
# long before MAX_DEPTH does -- and a RecursionError is a Python traceback, not
# a Vine error. Raise the ceiling high enough that our own guard wins.
PY_FRAMES_PER_CALL = 12
# And one level of a value costs a few more, on top of whatever the calls
# around it are holding. Both terms are in the ceiling below because both
# limits have to be able to fire: a 1000-deep value offered to `repr` inside
# 499 calls is the worst case either of them permits.
PY_FRAMES_PER_LEVEL = 4


class ReturnSignal(Exception):
    """A `return` on its way out to the call that will answer with it.

    Not a VineError and never rendered: it is control flow, not a failure.
    Nothing outside this module catches it and nothing needs to, because the
    parser refuses a `return` that has no function to leave -- so every
    signal raised has a `call()` below it that will take it. That refusal is
    what makes this exception unable to reach a user.
    """

    __slots__ = ("value",)

    def __init__(self, value):
        super().__init__()
        self.value = value


class Env:
    __slots__ = ("vars", "parent")

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def lookup(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise KeyError(name)

    def define(self, name, value):
        self.vars[name] = value


class Interpreter:
    def __init__(self, source, out=None):
        import sys

        self.source = source
        self.out = out if out is not None else sys.stdout
        self.depth = 0
        # Where the innermost expression still being evaluated was written,
        # and the calls it is inside, recorded only while a RecursionError is
        # on its way out. See `eval` and `call`.
        self.deep_pos = None
        self.deep_frames = []
        self.globals = Env()
        # The scope a program runs in. It outlives a single `run`, so a REPL
        # can feed this interpreter one entry at a time and keep its bindings.
        self.top = Env(self.globals)
        from .builtins import install

        install(self.globals)

    # -- error helper -----------------------------------------------------

    def fail(self, message, pos):
        raise RuntimeError_(message, pos, self.source)

    def key_for(self, value, pos):
        """A map key's slot in the dict underneath, or an error.

        Any value but a function may be one -- see `Composite keys` in
        docs/spec.md. The test is not the key's own type: a list of strings
        is a key and a list holding `print` is not, so what is asked is
        whether a function is anywhere inside it.
        """
        if type_name(value) == "function":
            raise RuntimeError_(
                "a map key may not be a function", pos, self.source
            ).help(KEY_RULE)
        if holds_function(value):
            err = RuntimeError_(
                f"a map key may not hold a function, got {type_name(value)}",
                pos,
                self.source,
            )
            err.note(f"the function is at {function_path(value)} inside the key")
            err.help(KEY_RULE)
            raise err
        return to_key(value)

    def overflowed(self, op, pos):
        raise RuntimeError_(
            f"the result of '{op}' is too large to be a float", pos, self.source
        ).help(FLOAT_CEILING)

    def widen(self, left, right, op, pos):
        """Check the int in a mixed int/float operation has a float to be.

        An operator with an int on one side and a float on the other converts
        the int, and an int may have more digits than a float can hold.
        Python does that conversion silently and raises OverflowError where it
        cannot, which left through '+', '-', '*' and '%' as a traceback. Only
        '/' caught it, and only because int / int raises there too. `float()`
        already refuses this int by name; an operator performing the same
        conversion owes the same answer.
        """
        if type_name(left) == type_name(right):
            return
        integer = left if type_name(left) == "int" else right
        try:
            float(integer)
        except OverflowError:
            raise RuntimeError_(
                "int is too large to convert to a float", pos, self.source
            ).note(
                f"'{op}' between an int and a float converts the int"
            ).help(FLOAT_CEILING) from None

    def finite(self, value, op, pos):
        """An arithmetic result, if Vine has one for it.

        Vine has no infinities, so overflow is an error rather than a value --
        the answer the language already gives for division by zero, and the
        one `repr` needs, since `inf` is not something a program can write.
        """
        if value in (INFINITY, -INFINITY):
            self.overflowed(op, pos)
        return value

    # -- entry point ------------------------------------------------------

    def run(self, program, source=None):
        """Evaluate `program` in the persistent top-level scope.

        `source` re-points error rendering at the text this program came from,
        for callers (the REPL) that evaluate many sources in one interpreter.
        """
        if source is not None:
            self.source = source
        with self.deep_enough():
            try:
                return self.eval_stmts(program, self.top)
            except TooDeep:
                # A walk stopped at `MAX_VALUE_DEPTH`. `MAX_DEPTH` counts
                # Vine *calls* and a 1001-deep list is built by 1001 shallow
                # ones, so this is the only guard a deep *value* meets.
                # `equal`, `canonical`, `holds_function`, `to_repr` and
                # `to_display` all walk a value to its bottom, and any of
                # them can reach here. The message says `value` for that
                # reason: an expression too deep is the parser's error and a
                # call too deep is `MAX_DEPTH`'s, and neither arrives here.
                raise self.deep_report(True, program.pos) from None
            except RecursionError:  # pragma: no cover - MAX_VALUE_DEPTH first
                raise self.deep_report(False, program.pos) from None

    def render(self, value, pos):
        """`repr` of a value, as a report rather than a traceback.

        The REPL echoes the value of every entry, and that echo is a walk
        like any other -- but it runs after `run` has returned, outside its
        ceiling and outside its handlers. Typing a deep value at a prompt
        ended the session in a Python traceback from the day the prompt
        existed, and `no_traceback.py` cannot see it: that property runs
        programs, and the echo is not part of one. Found in tick 33 by
        walking the new limit through every caller of `to_repr`.
        """
        with self.deep_enough():
            try:
                return to_repr(value)
            except TooDeep:
                raise self.deep_report(True, pos) from None
            except RecursionError:  # pragma: no cover - MAX_VALUE_DEPTH first
                raise self.deep_report(False, pos) from None

    @contextlib.contextmanager
    def deep_enough(self):
        """CPython's ceiling, raised so that Vine's own two limits fire first.

        Both terms are here because both limits have to be able to fire: a
        1000-deep value offered to `repr` inside 499 calls is the worst case
        either of them permits.
        """
        needed = (
            1000
            + MAX_DEPTH * PY_FRAMES_PER_CALL
            + MAX_VALUE_DEPTH * PY_FRAMES_PER_LEVEL
        )
        previous = sys.getrecursionlimit()
        if previous < needed:
            sys.setrecursionlimit(needed)
        try:
            yield
        finally:
            sys.setrecursionlimit(previous)

    def deep_report(self, counted, fallback):
        """The report for a walk that did not finish, at the position and
        under the call chain recorded on the way out.

        `counted` tells Vine's limit from the machine's, and they say
        different things on purpose: the uncounted one means the machine gave
        out *below* Vine's number, so the number is not what the reader hit
        and a help quoting it would be false. The pair is the one `parse()`
        already keeps for `MAX_NESTING`.

        Callers unwind past `eval` and `call`, which write `deep_pos` and
        `deep_frames` rather than building anything: on the `RecursionError`
        path they run at the depth that has just overflowed, where a call
        could overflow again. Nothing is built until here, where the stack is
        back.
        """
        pos = self.deep_pos if self.deep_pos is not None else fallback
        err = RuntimeError_(
            f"value nested more than {MAX_VALUE_DEPTH} deep"
            if counted
            else "value nested too deeply to work with",
            pos,
            self.source,
        )
        for label, at in self.deep_frames:
            err.frame(label, at)
        self.deep_pos, self.deep_frames = None, []
        return err.help(VALUE_DEPTH_RULE) if counted else err

    # -- evaluation -------------------------------------------------------

    def eval(self, node, env):
        method = self.DISPATCH.get(type(node))
        if method is None:  # pragma: no cover - guards against a missing case
            self.fail(f"cannot evaluate {type(node).__name__}", node.pos)
        try:
            return method(self, node, env)
        except (TooDeep, RecursionError):
            # A value under this node was too deep to walk. `run` turns that
            # into a Vine error, and by then there is nothing left on the
            # stack to say where it happened -- so the innermost evaluation
            # still running claims the position on the way past. Innermost
            # wins because it writes first and the `is None` keeps it.
            #
            # Nothing is built here on purpose. On the `RecursionError`
            # path this handler runs at the depth that has just overflowed,
            # so a call it made could overflow again; an attribute store
            # pushes no frame.
            if self.deep_pos is None:
                self.deep_pos = node.pos
            raise

    def eval_literal(self, node, env):
        return node.value

    def eval_strlit(self, node, env):
        """Every part converts the way `str` converts, so `"{x}"` and `str(x)`
        can never disagree -- and `repr` stays available as `"{repr(x)}"`."""
        return "".join(to_display(self.eval(part, env)) for part in node.parts)

    def eval_ident(self, node, env):
        try:
            return env.lookup(node.name)
        except KeyError:
            self.fail(f"undefined name '{node.name}'", node.pos)

    def eval_list(self, node, env):
        return [self.eval(item, env) for item in node.items]

    def eval_map(self, node, env):
        """A literal, and so the one place a key may be given twice by hand.

        Taking the last value is what a Python dict does and it discards a
        value the author wrote. `set` is the update; a literal is not one.
        The duplicate need not be visible either -- a parenthesised expression
        is a key, so `{(k): 1, region: 2}` collapses with nothing in the
        source looking repeated. See `Map order` in docs/spec.md.
        """
        out = {}
        first = {}
        for key_node, value_node in node.pairs:
            key = self.eval(key_node, env)
            slot = self.key_for(key, key_node.pos)
            if slot in first:
                err = RuntimeError_(
                    f"this map literal gives the key {to_repr(key)} twice",
                    key_node.pos,
                    self.source,
                )
                err.note("the key is first given at {pos}", first[slot])
                err.help(SET_RULE)
                raise err
            first[slot] = key_node.pos
            out[slot] = self.eval(value_node, env)
        return out

    def eval_block(self, node, env):
        """A block is its own scope; its value is that of its last statement."""
        return self.eval_stmts(node, Env(env))

    def eval_stmts(self, node, env):
        result = None
        for stmt in node.stmts:
            result = self.eval(stmt, env)
        return result

    def eval_let(self, node, env):
        env.define(node.name, self.eval(node.value, env))
        return None

    def eval_return(self, node, env):
        """Abandon the rest of the function and answer with this value.

        A bare `return` has no expression and answers `nil`, which is the
        value a function ending in a `let` already has.
        """
        value = None if node.value is None else self.eval(node.value, env)
        raise ReturnSignal(value)

    def eval_fn(self, node, env):
        return Function(node.params, node.body, env, node.name, node.pos)

    def eval_if(self, node, env):
        if is_truthy(self.eval(node.cond, env)):
            return self.eval(node.then, env)
        if node.otherwise is not None:
            return self.eval(node.otherwise, env)
        return None

    def eval_logical(self, node, env):
        left = self.eval(node.left, env)
        if node.op == "and":
            return self.eval(node.right, env) if is_truthy(left) else left
        return left if is_truthy(left) else self.eval(node.right, env)

    def eval_unary(self, node, env):
        value = self.eval(node.operand, env)
        if node.op == "not":
            return not is_truthy(value)
        if type_name(value) not in ("int", "float"):
            self.fail(f"cannot negate {type_name(value)}", node.pos)
        return -value

    def eval_binary(self, node, env):
        left = self.eval(node.left, env)
        right = self.eval(node.right, env)
        op = node.op
        if op == "==":
            return equal(left, right)
        if op == "!=":
            return not equal(left, right)
        lt, rt = type_name(left), type_name(right)
        numeric = {"int", "float"}
        if op == "+":
            if lt == "string" and rt == "string":
                return left + right
            if lt == "list" and rt == "list":
                return left + right
            if lt in numeric and rt in numeric:
                self.widen(left, right, op, node.pos)
                return self.finite(left + right, op, node.pos)
            self.fail(f"cannot add {lt} and {rt}", node.pos)
        if op in ("-", "*", "/", "%"):
            if lt not in numeric or rt not in numeric:
                self.fail(f"cannot apply '{op}' to {lt} and {rt}", node.pos)
            self.widen(left, right, op, node.pos)
            if op == "-":
                return self.finite(left - right, op, node.pos)
            if op == "*":
                return self.finite(left * right, op, node.pos)
            if right == 0:
                self.fail("division by zero", node.pos)
            if op == "/":
                try:
                    quotient = left / right
                except OverflowError:
                    # int / int whose quotient no float can hold. Python
                    # raises here and hands back inf everywhere else; the two
                    # mean one thing and get one report.
                    self.overflowed(op, node.pos)
                return self.finite(quotient, op, node.pos)
            return left % right
        if op in ("<", "<=", ">", ">="):
            comparable = (lt in numeric and rt in numeric) or (
                lt == "string" and rt == "string"
            )
            if not comparable:
                self.fail(f"cannot compare {lt} and {rt}", node.pos)
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            return left >= right
        self.fail(f"unknown operator '{op}'", node.pos)  # pragma: no cover

    def eval_index(self, node, env):
        target = self.eval(node.target, env)
        key = self.eval(node.key, env)
        kind = type_name(target)
        if kind == "list":
            if type_name(key) != "int":
                self.fail(f"list index must be an int, got {type_name(key)}", node.pos)
            index = key + len(target) if key < 0 else key
            if index < 0 or index >= len(target):
                self.fail(
                    f"index {key} is out of range for a list of length {len(target)}",
                    node.pos,
                )
            return target[index]
        if kind == "string":
            if type_name(key) != "int":
                self.fail(f"string index must be an int, got {type_name(key)}", node.pos)
            index = key + len(target) if key < 0 else key
            if index < 0 or index >= len(target):
                self.fail(
                    f"index {key} is out of range for a string of length {len(target)}",
                    node.pos,
                )
            return target[index]
        if kind == "map":
            slot = self.key_for(key, node.pos)
            if slot not in target:
                self.fail(f"{describe_map(target)} has no key {to_repr(key)}", node.pos)
            return target[slot]
        self.fail(f"cannot index {kind}", node.pos)

    def eval_call(self, node, env):
        callee = self.eval(node.callee, env)
        args = [self.eval(arg, env) for arg in node.args]
        return self.call(callee, args, node.pos)

    DISPATCH = {}

    # -- calling ----------------------------------------------------------

    def call(self, callee, args, pos):
        if isinstance(callee, Builtin):
            low, high = callee.arity
            if len(args) < low or (high is not None and len(args) > high):
                self.fail(
                    f"{callee.name} expects {describe_arity(low, high)}, "
                    f"got {len(args)}",
                    pos,
                )
            return callee.fn(self, pos, args)
        if isinstance(callee, Function):
            if len(args) != len(callee.params):
                err = RuntimeError_(
                    f"{callee.label} expects {plural(len(callee.params))}, "
                    f"got {len(args)}",
                    pos,
                    self.source,
                )
                if callee.pos is not None:
                    err.note(f"{callee.label} is defined at {{pos}}", callee.pos)
                raise err
            env = Env(callee.env)
            for name, value in zip(callee.params, args):
                env.define(name, value)
            self.depth += 1
            if self.depth > MAX_DEPTH:
                self.depth -= 1
                # The headline states the depth and stops there. It used to
                # end `(infinite recursion?)`, which was the only thing in
                # this report that was not a fact about the run and was
                # printed in the voice of one -- and the two goldens that
                # held it were both genuinely infinite, so the guess had
                # only ever been seen where it happened to be right. A
                # recursion that is correct and terminating reaches this
                # line too, as soon as the list it walks is longer than 500;
                # nothing here can tell the two apart, so nothing here says.
                # What the reader needs is the same either way, and it is a
                # rule of the language, so it is a help. See tick 36.
                raise RuntimeError_(
                    f"call nested more than {MAX_DEPTH} deep", pos, self.source
                ).help(CALL_DEPTH_RULE)
            try:
                return self.eval_stmts(callee.body, env)
            except ReturnSignal as signal:
                return signal.value
            except RuntimeError_ as err:
                # Where this failure came *from*. The caret is somewhere in
                # `callee`'s body, which the reader did not choose to be
                # looking at; `pos` is the call in their own text that put
                # them there. Recorded here rather than at the raise sites
                # because every one of them -- this module's, the builtins',
                # a nested call's -- leaves through here, and none of them
                # knows what called it. See VineError.frame().
                raise err.frame(callee.label, pos)
            except (TooDeep, RecursionError):
                # The same fact as the branch above, recorded rather than
                # framed: the error this belongs to does not exist yet, since
                # nothing may be built at the depth that has just overflowed.
                # `run` builds it and replays these in the order they arrive,
                # which is the order `frame` would have seen them.
                self.deep_frames.append((callee.label, pos))
                raise
            finally:
                self.depth -= 1
        self.fail(f"cannot call {type_name(callee)}", pos)


def describe_map(m):
    """`an empty map`, `a map of 1 key`, `a map of 4 keys`.

    The second clause of `map has no key K`, and the reason it is a count and
    not a list of the keys. A list's message names a *length* and never its
    elements, and a map's key set is the thing a length is: the crew already
    answered "name the container or summarise it" for lists, and this is the
    same answer. A partial list would be worse than none -- a reader told five
    of two hundred keys reads the five as the whole and concludes their key is
    absent from a set nobody showed them -- and a complete one is unbounded,
    so there is no threshold that is not arbitrary.

    What the count cannot do is what a length does: say which keys are valid.
    It discriminates the cases it can. An empty map is a bug upstream of the
    lookup, and a map of nine hundred keys where the reader expected three is
    the wrong variable; both used to read exactly like a missing key.
    """
    if not m:
        return "an empty map"
    return f"a map of {len(m)} key" + ("" if len(m) == 1 else "s")


def plural(n):
    return "1 argument" if n == 1 else f"{n} arguments"


def describe_arity(low, high):
    if high is None:
        return f"at least {plural(low)}"
    if low == high:
        return plural(low)
    return f"{low} to {high} arguments"


Interpreter.DISPATCH = {
    Literal: Interpreter.eval_literal,
    StrLit: Interpreter.eval_strlit,
    Ident: Interpreter.eval_ident,
    ListLit: Interpreter.eval_list,
    MapLit: Interpreter.eval_map,
    Block: Interpreter.eval_block,
    Let: Interpreter.eval_let,
    Return: Interpreter.eval_return,
    FnLit: Interpreter.eval_fn,
    If: Interpreter.eval_if,
    Logical: Interpreter.eval_logical,
    Unary: Interpreter.eval_unary,
    Binary: Interpreter.eval_binary,
    Index: Interpreter.eval_index,
    Call: Interpreter.eval_call,
}
