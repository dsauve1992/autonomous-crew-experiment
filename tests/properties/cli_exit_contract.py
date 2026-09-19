"""How `python3 -m vine` ends says truthfully what happened.

`docs/spec.md` promises three endings and nothing else: 0 when the program
ran, 1 when it failed with the report on stderr, and 2 when the command line
itself was the problem, reported as `error: ...` with no position. Each is
checkable from outside the process, which is the point of this file -- the CLI
is the one entry path `tests/properties/` cannot reach in-process, because a
property runs in-process and the CLI is a process per program. Its only guard
before this was `tests/cases/cli/running_it.cli`, seven hand-written command
lines, and the last Python traceback found on this path was found by hand, by
tick 7, reading `vine/cli.py` because nothing else would.

Nothing here is an expectation per command line: every check below is derived
from the run itself, so there is no table to keep in step with the code.

  - the status is one of the three, and never anything else
  - 0 means stderr is empty; the run had nothing to report
  - 1 means a Vine report -- a `<kind> error:` headline and a position line
  - 2 means one `error: ...` line and no position, because nothing was parsed
  - no `Traceback (most recent call last)` on either stream, ever

and one rule read off the command line rather than the run: a command line
naming more than one program to run -- two files, or `-e` and a file -- must
be a 2. It named two things and can do one; vine used to run the first and
exit 0 on the rest, which is a success status for half of what was asked.

This property spawns a process per command line, so it is a few seconds where
its neighbours are milliseconds. That is the reason it enumerates a few dozen
command lines and not a few thousand: the shapes that have actually broken,
plus both sides of every boundary `vine/cli.py` has.
"""

import os
import pathlib
import shlex
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

CLAIM = (
    "every vine command line exits 0 in silence, 1 with a positioned report, "
    "or 2 with a bare 'error:' line -- never a traceback, and never a success "
    "for a command line that names more than one program to run"
)

TRACEBACK = "Traceback (most recent call last)"
# Long enough that a hang is what it catches, short enough that a hung suite
# still finishes. Every command line below is milliseconds of real work.
TIMEOUT = 30

# Sources for `-e`, chosen for the ways a run has ended: quietly, loudly, in
# the lexer, in the parser, in the evaluator, and past the nesting guard --
# which is a third entry path for it, and the one no case covers.
EXPRESSIONS = [
    "print(1 + 1)",
    "1 + 1",
    "",
    "   ",
    "# just a comment",
    "1 / 0",
    "print(",
    'print("{")',
    "undefined_thing",
    'print("a")\nundefined_thing',
    "[" * 5000,
    "print(fixed(3 * 0.1, 2))",
]

# Files under tests/fixtures/, which exist in the repository.
GREET = "tests/fixtures/greet.vine"
BROKEN = "tests/fixtures/broken.vine"
LATIN1 = "tests/fixtures/latin1.vine"


def command_lines(scratch):
    """Every command line this property is checked against.

    `scratch` holds the files a repository cannot: one with no read
    permission, one whose name begins with a dash, and an empty one.
    """
    empty = str(scratch / "empty.vine")
    noread = str(scratch / "noread.vine")
    dashed = str(scratch / "-dash.vine")

    yield []                       # the REPL, with stdin already closed
    yield ["-e"]                   # an option with nothing after it
    for source in EXPRESSIONS:
        yield ["-e", source]
    yield ["--version"]
    yield ["-v"]
    yield ["--help"]
    yield ["-h"]
    yield ["--nope"]               # a flag vine does not have
    yield ["-x"]
    yield ["-"]
    yield ["--"]
    yield ["--", GREET]            # the usual escape, which vine has no rule for
    yield ["nosuchfile.vine"]
    yield ["tests/fixtures"]       # a directory given as a file
    yield [str(ROOT)]
    yield [empty]
    yield [noread]
    yield [dashed]
    yield [LATIN1]                 # not UTF-8: tick 7's traceback, still caught
    yield [GREET]
    yield [BROKEN]                 # prints, then fails
    yield [GREET, BROKEN]          # two files
    yield [GREET, "nosuchfile.vine"]
    yield ["-e", "print(1)", GREET]
    yield [GREET, "-e", "print(1)"]
    yield ["-e", "print(1)", "-e", "print(2)"]
    yield ["-e", "print(1)", "-e"]
    yield [GREET, GREET, GREET]


def programs_named(argv):
    """How many programs a command line asks vine to run.

    Read off the arguments, not off vine: `-e` takes the word after it, and
    anything else is a file name. Command lines that ask for no program at all
    -- `--help`, `--version` -- are not counted here and are excluded by the
    caller, because a question about vine is not a program.
    """
    count, i = 0, 0
    while i < len(argv):
        if argv[i] == "-e":
            if i + 1 >= len(argv):
                return count  # `-e` with nothing after it names no program
            count += 1
            i += 2
        else:
            count += 1
            i += 1
    return count


def asks_a_question(argv):
    return any(a in ("-h", "--help", "-v", "--version") for a in argv)


def broken_by(argv, done):
    """What this run did that the claim forbids, or None."""
    out, err = done.stdout, done.stderr
    if TRACEBACK in err or TRACEBACK in out:
        line = next(l for l in (err + out).splitlines() if TRACEBACK in l)
        return f"a Python traceback reached the user: {line.strip()}"
    if done.returncode not in (0, 1, 2):
        return f"exit {done.returncode}, which is none of the three"
    if done.returncode == 0:
        if err:
            return f"exit 0, but stderr says {err.splitlines()[0]!r}"
    elif done.returncode == 1:
        if not err:
            return "exit 1 with nothing on stderr: a failure it did not report"
        head = err.splitlines()[0]
        if "error: " not in head:
            return f"exit 1, but the report opens {head!r}, which names no kind of error"
        if "\n --> " not in err:
            return f"exit 1, but the report carries no position: {err!r}"
    else:
        if not err.startswith("error: "):
            return f"exit 2, but stderr opens {err.splitlines()[0]!r} rather than 'error: '"
        if " --> " in err:
            return f"exit 2, but the report carries a position: {err!r}"
    if not asks_a_question(argv) and programs_named(argv) > 1:
        if done.returncode != 2:
            return (
                f"names {programs_named(argv)} programs to run and exited "
                f"{done.returncode}: only the first was run"
            )
    return None


def check():
    """Returns (how many command lines were checked, the ones that broke it)."""
    failures = []
    checked = 0
    with tempfile.TemporaryDirectory() as scratch_name:
        scratch = pathlib.Path(scratch_name)
        (scratch / "empty.vine").write_text("")
        (scratch / "-dash.vine").write_text("print(1)\n")
        noread = scratch / "noread.vine"
        noread.write_text("print(1)\n")
        # Root can read it anyway, in which case the file simply runs and the
        # claim still holds -- one fewer shape reached, not a false failure.
        os.chmod(noread, 0)
        for argv in command_lines(scratch):
            checked += 1
            printable = "vine " + " ".join(shlex.quote(a) for a in argv)
            try:
                done = subprocess.run(
                    [sys.executable, "-m", "vine", *argv],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                    timeout=TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                failures.append((printable, f"did not finish in {TIMEOUT}s"))
                continue
            broke = broken_by(argv, done)
            if broke is not None:
                failures.append((printable, broke))
        os.chmod(noread, 0o600)
    return checked, failures
