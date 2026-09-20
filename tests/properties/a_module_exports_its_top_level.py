"""A module's map is its top-level `let`s, and a `do` block is how it hides one.

**Importing** says every top-level binding a file makes is in the map it
answers with, and offers one remedy to a file that wants a private helper:
"put it inside the function that needs it". `a_module_keeps_its_scope.py`
already checks the first half over a two-name module written for it. This
checks it over the **modules in this repository**, and checks the remedy --
both the one the document named and the cheaper one it already contained four
paragraphs earlier and did not connect.

## Why the corpus and not another synthetic module

A synthetic module is written by whoever is writing the check, so it holds the
names they thought of. `examples/clock.vine` exports seven names and its
caller uses three, and the four it did not mean to hand out include `dates` --
an import handle, which is a top-level binding like any other. Nobody could
have predicted that shape; it came out of a program. So clause 1 reads the
real files, and its second side is the **parser**: the top-level `Let` nodes
of the file's own AST, against the keys the **interpreter** answers with. Two
mechanisms, one claim -- a module that gained a builtin, dropped a name,
reordered them, or leaked a name bound inside a `do` block or a function body
would fail here and pass every golden in the repository.

## Three clauses

1. **Over every module in the corpus**, `keys(import "f")` is exactly the
   names its top-level `let`s bind, in source order, a name bound twice
   counting once at its first position.
2. **A `do` block hides, and so does a function body, and a top-level `let`
   does not.** One module written three ways over the same helper. This is
   the sentence **Importing** now makes: a `do` block is a scope that runs
   once, so a helper several exported functions share can be private without
   being rebuilt per call.
3. **A re-binding re-exports.** `let pad = other.pad` at a module's top level
   puts `pad` in *this* module's map. **Importing**'s two "What this does not
   add" paragraphs disagreed about this for a tick: one offers picking a name
   out of the map as the reason selective import is unnecessary, the other
   says every top-level binding is exported. Inside a module those are the
   same sentence twice with opposite advice, and this clause is the half
   nothing was watching.

## Sabotage, each run against the committed tree, and each run to the end

Written from reasoning first and then run, which is how two of the three
turned out to be wrong about their own blast radius.

- `module_env.vars` in `Interpreter.load` replaced by the whole **chain** --
  every name the module can *see* rather than every name it bound -- breaks
  **7 of 7**, not the five predicted. Every clause names the 33 builtins, and
  so does clause 3 of `a_module_keeps_its_scope.py`, which is the same claim
  over its own module. Two properties, and between them the only thing they
  agree about is which one reads the corpus.
- A `do` block evaluated in the enclosing environment rather than a child of
  it breaks **1 of 7** -- clause 2's `do` case alone, `secret` arriving in the
  map beside `answer` -- exactly as predicted. What was not predicted is that
  the repository already catches this sabotage three other ways:
  `tests/cases/blocks.vine`, `tests/cases/rebinding.vine` and
  `spec_examples_run.py` all break with it. So this clause does not discover
  that a `do` block is a scope; it is the only thing that says a `do` block
  keeps a name **out of a module's map**, which is what **Importing** now
  recommends it for and what no case here depended on before.
- The order of `keys` reversed breaks **5 of 7**, not the four predicted:
  clause 1 on all three modules, clause 2's two-name module, and clause 3,
  which was written as though it named one key and names three.

What this does not check: whether a module *should* export what it exports.
That is a judgement about a program and no property holds one. What it holds
is that the list is the one the file wrote, so a reader counting exports is
counting something.
"""

import pathlib
import tempfile

from vine import run
from vine.errors import Source
from vine.nodes import Let
from vine.parser import parse
from vine.values import to_repr

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

CLAIM = (
    "a module's map holds exactly the names its top level bound, in the order "
    "it bound them -- so a `do` block or a function body hides a helper and a "
    "re-binding of a borrowed name exports it"
)

# The files in this repository that another file imports. Named rather than
# globbed: a module is a file somebody imports, and globbing `examples/*.vine`
# would sweep in the seven programs, which export whatever their last `let`
# happened to be and mean nothing by it.
MODULES = [
    "examples/table.vine",
    "examples/dates.vine",
    "examples/clock.vine",
]


def top_level_lets(path):
    """The names the file's top-level `let`s bind, first position wins.

    The parser's own AST, so this is not a second reading of the source with a
    regular expression -- a `let` inside a `do` block or a function body is a
    statement of *that* block and never appears here.
    """
    text = (ROOT / path).read_text(encoding="utf-8")
    program = parse(Source(text, pathlib.Path(path).name))
    names = []
    for stmt in program.stmts:
        if isinstance(stmt, Let) and stmt.name not in names:
            names.append(stmt.name)
    return names


def keys_of(path):
    """What `keys(import "<path>")` answers, run from beside the file."""
    name = pathlib.Path(path).name
    source = f'keys(import "{name}")\n'
    origin = ROOT / pathlib.Path(path).parent / "<exports>.vine"
    return run(source, "<exports>", origin=origin)


def answer(directory, files, program):
    """Write `files` into `directory` and answer what `program` gives back."""
    for name, text in files.items():
        (directory / name).write_text(text, encoding="utf-8")
    return to_repr(run(program, "<exports>", origin=directory / "<exports>.vine"))


# Clause 2. One helper, three places to put it, and the same answer from all
# three -- so the only thing that differs is the map.
HIDING = {
    "at the top level": (
        "let secret = fn() { 7 }\nlet answer = fn() { secret() }\n",
        '["secret", "answer"]',
    ),
    "inside a do block": (
        "let answer = do {\n"
        "  let secret = fn() { 7 }\n"
        "  fn() { secret() }\n"
        "}\n",
        '["answer"]',
    ),
    "inside the function that needs it": (
        "let answer = fn() {\n  let secret = fn() { 7 }\n  secret()\n}\n",
        '["answer"]',
    ),
}


def check():
    checked = 0
    failures = []

    for path in MODULES:
        checked += 1
        want = top_level_lets(path)
        got = keys_of(path)
        if got != want:
            failures.append((
                f"the map {path} answers with",
                f"holds {got}, not {want} -- a module's map is the names its "
                "top level bound, in the order it bound them",
            ))

    with tempfile.TemporaryDirectory() as tmp:
        directory = pathlib.Path(tmp)

        for where, (module, want_keys) in HIDING.items():
            checked += 1
            got = answer(
                directory,
                {"mod.vine": module},
                'let m = import "mod.vine"\n[keys(m), m.answer()]\n',
            )
            want = f"[{want_keys}, 7]"
            if got != want:
                failures.append((
                    f"a module with its helper {where}",
                    f"answers {got}, not {want} -- a scope that is not the "
                    "file's top level is not in the file's map, and the "
                    "helper still works from inside it",
                ))

        checked += 1
        got = answer(
            directory,
            {
                "other.vine": "let pad = fn(s) { s + \"!\" }\n",
                "mod.vine": 'let other = import "other.vine"\n'
                "let pad = other.pad\n"
                "let shout = fn(s) { pad(s) }\n",
            },
            'let m = import "mod.vine"\nkeys(m)\n',
        )
        want = '["other", "pad", "shout"]'
        if got != want:
            failures.append((
                "a module that re-binds a name it borrowed",
                f"answers {got}, not {want} -- `let pad = other.pad` is a "
                "top-level binding, so a module that re-binds what it borrowed "
                "re-exports it, and the import handle with it",
            ))

    return checked, failures
