"""Command line entry point."""

import sys

from . import __version__, run
from .errors import VineError
from .interp import FailSignal

USAGE = """usage: vine [options] [file]

  vine                 open an interactive session
  vine script.vine     run a file
  vine -e 'EXPR'       run a single line of source
  vine --version       print the version
"""


# Vine has no option past the three above, so an argument beginning with a
# dash is a file name like any other -- which is why `vine -x.vine` runs a
# file called -x.vine, and why vine needs no `--` to let it. The rule is true
# and invisible: a reader who mistypes a flag is told the file system is
# missing something. It goes in a help, because a rule of the language is what
# a help is for, and the headline above it stays a fact.
#
# The `` = help: `` prefix is spelt out here rather than rendered: these errors
# have no position and so no VineError to hang notes on. If `note_lines()` in
# errors.py ever changes shape, this line has to follow it.
OPTIONS_RULE = (
    " = help: vine's options are -e, -h/--help and -v/--version; "
    "any other argument is a file name\n"
)


def option_rule(names):
    """The rule above, when something here could be mistaken for an option."""
    return OPTIONS_RULE if any(name.startswith("-") for name in names) else ""


def listing(programs):
    """Name each program a command line asked for, as the reader wrote it.

    A file is quoted the way every other Vine message quotes a name; `-e` is
    the option itself, because the expression after it is the reader's and
    repeating it back in a refusal is noise.
    """
    names = ["-e" if kind == "-e" else f"'{argument}'" for kind, argument in programs]
    return ", ".join(names[:-1]) + " and " + names[-1]


def stdin_text():
    """The program's standard input, decoded -- what `read()` answers with.

    Handed to `run` unevaluated, so a program that never calls `read()` never
    touches the pipe it is on. A terminal is the one input there is no point
    waiting for: nothing was redirected in, and a report that sat there
    looking frozen would be worse than the refusal `read()` gives instead.
    The UnicodeDecodeError this may raise is caught in `read()`, which has a
    position to hang the message on and this does not.
    """
    if sys.stdin is None or sys.stdin.isatty():
        return None
    return sys.stdin.buffer.read().decode("utf-8")


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
            + option_rule([argument for _, argument in programs])
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
            sys.stderr.write(
                f"error: cannot read {name}: {exc.strerror}\n" + option_rule([name])
            )
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
        run(text, name, inp=stdin_text)
    except VineError as exc:
        sys.stderr.write(exc.render() + "\n")
        return 1
    except FailSignal as refusal:
        # A refusal is a 1, the same status a runtime error gets, because the
        # shell's question is only ever "is there a report I can use?" and
        # both answer no. What differs is the voice: this is the program's own
        # sentence about its data, with no position, where the line above is a
        # diagnostic about the program with a caret in it. It is not a 2 --
        # that status is the command line's, and a command line that named a
        # readable program and one input was not the problem.
        sys.stderr.write(refusal.text + "\n")
        return 1
    return 0
