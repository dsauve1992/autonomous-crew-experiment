"""Command line entry point."""

import sys

from . import __version__, run
from .errors import VineError

USAGE = """usage: vine [options] [file]

  vine                 open an interactive session
  vine script.vine     run a file
  vine -e 'EXPR'       run a single line of source
  vine --version       print the version
"""


def main(argv):
    if not argv:
        from .repl import repl

        return repl()
    if argv[0] in ("-h", "--help"):
        sys.stdout.write(USAGE)
        return 0
    if argv[0] in ("-v", "--version"):
        sys.stdout.write(f"vine {__version__}\n")
        return 0

    if argv[0] == "-e":
        if len(argv) < 2:
            sys.stderr.write("error: -e needs an expression\n")
            return 2
        text, name = argv[1], "<argument>"
    else:
        name = argv[0]
        try:
            with open(name, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            sys.stderr.write(f"error: cannot read {name}: {exc.strerror}\n")
            return 2

    try:
        run(text, name)
    except VineError as exc:
        sys.stderr.write(exc.render() + "\n")
        return 1
    return 0
