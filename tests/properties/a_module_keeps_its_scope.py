"""An imported file's names are its own, in both directions.

This is the one decision `import` makes, and **Importing** stakes the whole
feature on it: an imported file runs in a scope that is a *sibling* of the
importing file's rather than a child of it, so its functions close over it and
nothing outside can reach in. The alternative -- binding the other file's
names into this one's scope -- is textual inclusion, which **Bindings** makes
unsafe: a second `let` on a name replaces the first *and closures made earlier
see the new value*, so a program that imported `pad` and then bound a `spaces`
of its own would silently change what `pad` does, and the report would be a
column of dots in a table.

`tests/cases/import.vine` is that story as a golden, with one name. One name
is where a scope bug hides: `Env(self.globals)` written as `self.top`, or as
`Env()`, or a module's bindings written back into `globals`, are three
one-word slips and the first two pass any single-name case that does not
happen to use the name they break.

So the sweep is over the *builtins*, which are the 33 names every file starts
with and the only names two files are guaranteed to share. Two clauses, one
per direction, and a third about the map:

1. **A module may shadow a builtin, and the importer keeps the builtin.**
   The module binds the name to a string; from inside the module the name is
   the string, from the importer it is still the builtin, and the module's
   value is reachable only through the map.
2. **An importer may shadow a builtin, and the module keeps the builtin.**
   The module's function is written before the importer's `let` exists and
   must not see it. Measured, on two sabotages: `module_env = self.top` in
   `load()` breaks 66 of the 67 -- both clauses on all 33 names, with clause 3
   the survivor -- and `Env()` in place of `Env(self.globals)` breaks exactly
   the 33 of clause 2, because a module with no builtins cannot call `str`
   and clause 1's module calls nothing. Reading those two outputs is also
   what rewrote `answer`; see it.
3. **The map is exactly the names the file bound.** Not more -- the 33
   builtins are in scope for a module and are not its bindings, and a map that
   carried them would put `len` on every module in the language.

`str` is how a builtin is told from anything else: it renders `<builtin len>`,
which no Vine value can be mistaken for. The programs are compared by the
value the last statement answers rather than by what they print, because
`print` is one of the 33 and a program that has just shadowed it cannot use
it.
"""

import pathlib
import tempfile

from vine import run
from vine.errors import VineError
from vine.builtins import install
from vine.interp import Env
from vine.values import to_repr

CLAIM = (
    "an imported file's top-level names are its own: shadowing a builtin in "
    "one file does not change what the other sees, and the map an import "
    "answers with holds the file's bindings and nothing else"
)


def builtins():
    env = Env()
    install(env)
    return sorted(env.vars)


# What the module binds in clause 3, and what its map must then hold.
ROSTER = "let a = 1\nlet b = fn() { a }\nlet a = 2\n"


def answer(directory, module, program):
    """What `program` answers when `module` is the file beside it, as source.

    A report rather than an exception, because a scope bug does not politely
    answer the wrong value. Before this caught anything, both sabotages in the
    docstring above ended the whole property in a Python traceback on their
    first program -- `cannot call string`, for a module whose `let concat =
    "shadowed"` had landed in the importer's scope -- and it reported
    `0 broke it, of 0 checked`, which names no value and finds nothing. With
    the report as the answer, the same two sabotages name 66 and 33. Found by
    reading the sabotage's output rather than its exit status.

    The name given to `run` is not a real file; only its directory is used,
    and that is where the module was written.
    """
    (directory / "mod.vine").write_text(module, encoding="utf-8")
    try:
        return to_repr(run(program, "<scope>", origin=directory / "<scope>.vine"))
    except VineError as error:
        return error.render().splitlines()[0]


def check():
    checked = 0
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        directory = pathlib.Path(tmp)

        for name in builtins():
            checked += 1
            got = answer(
                directory,
                f'let {name} = "shadowed"\nlet mine = fn() {{ {name} }}\n',
                f'let m = import "mod.vine"\n[m.{name}, m.mine(), str({name})]\n',
            )
            want = f'["shadowed", "shadowed", "<builtin {name}>"]'
            if got != want:
                failures.append((
                    f"a module binding '{name}'",
                    f"answers {got}, not {want} -- the module's "
                    "binding and the importer's builtin are one name in two "
                    "scopes",
                ))

            checked += 1
            got = answer(
                directory,
                f"let mine = fn() {{ str({name}) }}\n",
                f'let m = import "mod.vine"\n'
                f'let {name} = "caller"\n[m.mine(), {name}]\n',
            )
            want = f'["<builtin {name}>", "caller"]'
            if got != want:
                failures.append((
                    f"an importer binding '{name}'",
                    f"answers {got}, not {want} -- the module was "
                    "written before this binding existed and must not see it",
                ))

        checked += 1
        got = answer(
            directory, ROSTER, 'let m = import "mod.vine"\n[keys(m), m.b()]\n'
        )
        want = '[["a", "b"], 2]'
        if got != want:
            failures.append((
                "the map of a module binding 'a', 'b' and 'a' again",
                f"is {got}, not {want} -- a module's map is the "
                "names it bound, in the order it bound them, and a name bound "
                "twice is one key holding the second value",
            ))

    return checked, failures
