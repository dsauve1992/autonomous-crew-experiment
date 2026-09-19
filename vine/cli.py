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


def listing(programs):
    """Name each program a command line asked for, as the reader wrote it.

    A file is quoted the way every other Vine message quotes a name; `-e` is
    the option itself, because the expression after it is the reader's and
    repeating it back in a refusal is noise.
    """
    names = ["-e" if kind == "-e" else f"'{argument}'" for kind, argument in programs]
    return ", ".join(names[:-1]) + " and " + names[-1]


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

    programs = []
    i = 0
    while i < len(argv):
        if argv[i] == "-e":
            if i + 1 >= len(argv):
                sys.stderr.write("error: -e needs an expression\n")
                return 2
            programs.append(("-e", argv[i + 1]))
            i += 2
        else:
            programs.append(("file", argv[i]))
            i += 1
    if len(programs) > 1:
        # Running the first and ignoring the rest exits 0 -- a success status
        # for half of what was asked, which is worse than any refusal. Found
        # by tests/properties/cli_exit_contract.py on its first run.
        sys.stderr.write(
            f"error: vine runs one program at a time, but {len(programs)} "
            f"were given: {listing(programs)}\n"
        )
        return 2

    kind, argument = programs[0]
    if kind == "-e":
        text, name = argument, "<argument>"
    else:
        name = argument
        try:
            with open(name, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            sys.stderr.write(f"error: cannot read {name}: {exc.strerror}\n")
            return 2
        except UnicodeDecodeError as exc:
            # Vine source is UTF-8. A file that is not -- a binary, or a
            # program saved in another encoding -- fails inside read(), and
            # UnicodeDecodeError is a ValueError rather than an OSError, so
            # the handler above let it out as a Python traceback.
            sys.stderr.write(
                f"error: cannot read {name}: not UTF-8 text "
                f"(byte 0x{exc.object[exc.start]:02x} at offset {exc.start})\n"
            )
            return 2

    try:
        run(text, name)
    except VineError as exc:
        sys.stderr.write(exc.render() + "\n")
        return 1
    return 0
