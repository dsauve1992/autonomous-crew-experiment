"""The tree-walking evaluator."""

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
    Unary,
)
from .values import Builtin, Function, equal, is_truthy, to_repr, type_name

# How deep Vine calls may nest before we call it runaway recursion.
MAX_DEPTH = 500
# One Vine call costs several Python frames, so CPython's own limit would fire
# long before MAX_DEPTH does -- and a RecursionError is a Python traceback, not
# a Vine error. Raise the ceiling high enough that our own guard wins.
PY_FRAMES_PER_CALL = 12


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
        self.globals = Env()
        # The scope a program runs in. It outlives a single `run`, so a REPL
        # can feed this interpreter one entry at a time and keep its bindings.
        self.top = Env(self.globals)
        from .builtins import install

        install(self.globals)

    # -- error helper -----------------------------------------------------

    def fail(self, message, pos):
        raise RuntimeError_(message, pos, self.source)

    # -- entry point ------------------------------------------------------

    def run(self, program, source=None):
        """Evaluate `program` in the persistent top-level scope.

        `source` re-points error rendering at the text this program came from,
        for callers (the REPL) that evaluate many sources in one interpreter.
        """
        import sys

        if source is not None:
            self.source = source
        needed = 1000 + MAX_DEPTH * PY_FRAMES_PER_CALL
        previous = sys.getrecursionlimit()
        if previous < needed:
            sys.setrecursionlimit(needed)
        try:
            return self.eval_stmts(program, self.top)
        except RecursionError:  # a belt-and-braces net; MAX_DEPTH should win
            raise RuntimeError_(
                "evaluation nested too deeply", program.pos, self.source
            ) from None
        finally:
            sys.setrecursionlimit(previous)

    # -- evaluation -------------------------------------------------------

    def eval(self, node, env):
        method = self.DISPATCH.get(type(node))
        if method is None:  # pragma: no cover - guards against a missing case
            self.fail(f"cannot evaluate {type(node).__name__}", node.pos)
        return method(self, node, env)

    def eval_literal(self, node, env):
        return node.value

    def eval_ident(self, node, env):
        try:
            return env.lookup(node.name)
        except KeyError:
            self.fail(f"undefined name '{node.name}'", node.pos)

    def eval_list(self, node, env):
        return [self.eval(item, env) for item in node.items]

    def eval_map(self, node, env):
        out = {}
        for key_node, value_node in node.pairs:
            key = self.eval(key_node, env)
            if type_name(key) not in ("string", "int", "float", "bool"):
                self.fail(
                    f"map key must be a string, number or bool, got {type_name(key)}",
                    key_node.pos,
                )
            out[key] = self.eval(value_node, env)
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

    def eval_fn(self, node, env):
        return Function(node.params, node.body, env, node.name)

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
                return left + right
            self.fail(f"cannot add {lt} and {rt}", node.pos)
        if op in ("-", "*", "/", "%"):
            if lt not in numeric or rt not in numeric:
                self.fail(f"cannot apply '{op}' to {lt} and {rt}", node.pos)
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if right == 0:
                self.fail("division by zero", node.pos)
            if op == "/":
                return left / right
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
            if key not in target:
                self.fail(f"map has no key {to_repr(key)}", node.pos)
            return target[key]
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
                self.fail(
                    f"{callee.label} expects {plural(len(callee.params))}, "
                    f"got {len(args)}",
                    pos,
                )
            env = Env(callee.env)
            for name, value in zip(callee.params, args):
                env.define(name, value)
            self.depth += 1
            if self.depth > MAX_DEPTH:
                self.depth -= 1
                self.fail(
                    f"call depth exceeded {MAX_DEPTH} (infinite recursion?)", pos
                )
            try:
                return self.eval_stmts(callee.body, env)
            finally:
                self.depth -= 1
        self.fail(f"cannot call {type_name(callee)}", pos)


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
    Ident: Interpreter.eval_ident,
    ListLit: Interpreter.eval_list,
    MapLit: Interpreter.eval_map,
    Block: Interpreter.eval_block,
    Let: Interpreter.eval_let,
    FnLit: Interpreter.eval_fn,
    If: Interpreter.eval_if,
    Logical: Interpreter.eval_logical,
    Unary: Interpreter.eval_unary,
    Binary: Interpreter.eval_binary,
    Index: Interpreter.eval_index,
    Call: Interpreter.eval_call,
}
