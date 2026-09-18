"""The interactive session: read an entry, evaluate it, show its value.

Three decisions worth knowing before reading the code, all of them recorded in
docs/spec.md as well:

- An entry's value is shown with `repr` unless it is nil. `let` and `print`
  both evaluate to nil, and they are most of what anyone types at a prompt;
  echoing `nil` after each of them is noise. Silence therefore means nil.
- Bindings persist because the whole session shares one interpreter, and so
  one top-level scope. Re-binding a name just shadows the old value, exactly
  as a second `let` in one scope does in a file.
- An entry that ends mid-expression is continued rather than rejected. The
  parser already distinguishes "ran out of input" from "found the wrong
  thing"; this reads that flag and nothing more, so the REPL never needs its
  own idea of what a finished expression looks like.
"""

import sys

from . import __version__
from .errors import Source, SyntaxError_, VineError
from .interp import Interpreter
from .parser import parse
from .values import to_repr

PROMPT = ">>> "
CONTINUE = "... "
BANNER = f"vine {__version__} — ^D to exit, blank line to abandon an unfinished entry"


class Repl:
    def __init__(self, inp=None, out=None, interactive=None):
        self.inp = inp if inp is not None else sys.stdin
        self.out = out if out is not None else sys.stdout
        if interactive is None:
            interactive = self.inp.isatty()
        self.interactive = interactive
        self.interp = Interpreter(Source("", "<repl>"), self.out)
        self.entries = 0
        self.buffer = []

    # -- input and output -------------------------------------------------

    def write(self, text):
        self.out.write(text)
        self.out.flush()

    def read(self, prompt):
        """One line of input, or None at end of input.

        At a terminal the prompt goes out before the line is read, and the
        terminal echoes what is typed. From a pipe nothing echoes, so the
        prompt is written *with* the line it belongs to instead. The result is
        that a piped session produces the transcript a person would have seen,
        which is what makes it reviewable as a golden file.
        """
        if self.interactive:
            self.write(prompt)
        line = self.inp.readline()
        if line == "":
            return None
        line = line.rstrip("\n")
        if not self.interactive:
            # Right-stripped so a transcript never carries trailing whitespace:
            # golden files are compared byte for byte, and trailing spaces are
            # exactly what an editor or a tool silently eats.
            self.write((prompt + line).rstrip() + "\n")
        return line

    # -- the loop ---------------------------------------------------------

    def run(self):
        self.write(BANNER + "\n")
        while True:
            try:
                if not self.step():
                    return 0
            except KeyboardInterrupt:
                # Ctrl-C abandons what is half-typed or half-running and hands
                # the prompt back. It does not end the session, and it must not
                # reach the user as a Python traceback.
                self.buffer = []
                self.write("\n^C\n")

    def step(self):
        """Read and handle one line. Returns False at end of input."""
        line = self.read(CONTINUE if self.buffer else PROMPT)
        if line is None:
            if self.interactive:
                self.write("\n")
            return False
        if line.strip() == "":
            self.buffer = []  # nothing pending, or abandon what is pending
            return True

        self.buffer.append(line)
        source = Source("\n".join(self.buffer), f"<repl:{self.entries + 1}>")
        try:
            program = parse(source)
        except SyntaxError_ as exc:
            if exc.at_eof:
                return True  # unfinished, not wrong: keep the buffer and ask
            self.finish()
            self.write(exc.render() + "\n")
            return True
        self.finish()

        try:
            value = self.interp.run(program, source)
        except VineError as exc:
            self.write(exc.render() + "\n")
            return True
        if value is not None:
            self.write(to_repr(value) + "\n")
        return True

    def finish(self):
        """This entry is over, one way or the other."""
        self.buffer = []
        self.entries += 1


def repl(inp=None, out=None, interactive=None):
    return Repl(inp, out, interactive).run()
