"""How `python3 -m vine` ends says truthfully what happened.

`docs/spec.md` promises three endings and nothing else: 0 when the program
ran, 1 when it failed with something on stderr saying so, and 2 when the
command line itself was the problem, reported as `error: ...` with no
position. Each is checkable from outside the process, which is the point of
this file -- the CLI
is the one entry path `tests/properties/` cannot reach in-process, because a
property runs in-process and the CLI is a process per program. Its only guard
before this was `tests/cases/cli/running_it.cli`, seven hand-written command
lines, and the last Python traceback found on this path was found by hand, by
tick 7, reading `vine/cli.py` because nothing else would.

Nothing here is an expectation per command line: every check below is derived
from the run itself, so there is no table to keep in step with the code.

  - the status is one of the three, and never anything else
  - 0 means stderr is empty; the run had nothing to report
  - 1 means stderr carries a visible character -- not merely a byte, which
    is what `fail ""` produced past this clause until tick 42 -- in one of
    its two voices: a Vine report --
    a `<kind> error:` headline *and* a position line -- or a refusal, which
    is the program's own sentence and carries neither. Half of either is the
    failure this catches: a headline with no position under it is a report
    that lost one, and a position under a sentence that names no kind of
    error is a report that lost its head.
  - 2 means one `error: ...` line and no position, because nothing was parsed
  - no `Traceback (most recent call last)` on either stream, ever

and one rule read off the command line rather than the run: a command line
naming more than one program to run -- two files, or `-e` and a file -- must
be a 2. It named two things and can do one; vine used to run the first and
exit 0 on the rest, which is a success status for half of what was asked.

A fourth clause, about the document rather than the runs: **the statuses
these command lines produce are exactly the ones the paragraph in **Errors**
names.** That paragraph is where the three endings are promised, and until
this clause it was held by nobody -- this file quoted it in prose above, which
is a copy and not a check. The shape is tick 26's: `return` became a keyword,
the Keywords line went false, and a hundred and fifty-two checks stayed green
over it. A status vine can return and the document does not name is an
undocumented ending; one the document names that nothing here produces is a
promise the implementation dropped, or a command line this file stopped
enumerating. Both directions, for `help_roster.py`'s reason.

The 1 clause tells the two voices apart by the headline, and that is a reading
of the command lines below rather than a law about every program there could
be: `fail "runtime error: x"` is legal Vine and would be read here as a
report. That is the scope this file has always had -- a few dozen chosen
command lines, not a sweep -- and the alternative is a clause that asks a
program what it meant to write.

This property spawns a process per command line, so it is a few seconds where
its neighbours are milliseconds. That is the reason it enumerates a few dozen
command lines and not a few thousand: the shapes that have actually broken,
plus both sides of every boundary `vine/cli.py` has.
"""

import os
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

CLAIM = (
    "every vine command line exits 0 in silence, 1 with either a positioned "
    "report or a refusal carrying no position, or 2 with a bare 'error:' "
    "line -- never a traceback, and never a success for a command line that "
    "names more than one program to run"
)

TRACEBACK = "Traceback (most recent call last)"
# What a Vine report opens with. `error: ` alone is the command line's shape
# and belongs to a 2; anything else on a failing run's stderr is a refusal.
REPORT_HEAD = re.compile(r"^(syntax|runtime) error: ")
SPEC = ROOT / "docs" / "spec.md"
# The paragraph in **Errors** that promises the endings, and the numbers in
# it. Anchored on its first words rather than found by the numbers alone:
# `exits 0` and `exit 1` appear in five other places in that document, each
# about one ending rather than about the set of them.
PARAGRAPH = "Running a file exits"
STATUS = re.compile(r"\bexits (\d+)\b")
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
    # The refusal, and the ways out of one. A `fail` leaves through whatever
    # is above it -- nothing, a call, a builtin calling back into Vine -- and
    # the last two are the paths that would be swallowed by a handler that
    # was written for `return`.
    'fail "no rows to report"',
    'print("half a report")\nfail "and no more"',
    "fail",                       # the one statement with no bare form
    "fail 1 / 0",                 # the message's own expression failing first
    'let f = fn() { fail "out through a call" }\nf()',
    'map([1], fn(x) { fail "out through a builtin" })',
    # A message the grammar cannot see is missing. The rule that refuses a
    # bare `fail` is about the ending, not about the source, so it has to
    # reach these two as well -- and until tick 42 it did not.
    'fail ""',
    'fail "   "',
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


def documented_statuses():
    """The endings **Errors** promises, read out of the document.

    Returns None if the paragraph is not where this expects it, which is a
    failure of its own: a property that reads a document and finds nothing
    reads nothing, and passes.
    """
    lines = SPEC.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(PARAGRAPH)]
    if len(starts) != 1:
        return None
    body = []
    for line in lines[starts[0]:]:
        if not line.strip():
            break
        body.append(line)
    return {int(n) for n in STATUS.findall(" ".join(body))}


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
        if not err.strip():
            # `not err` was the test until tick 42, and `fail ""` walked
            # through it: a 1 whose stderr is one newline is the ending
            # **Errors** forbids, arriving with a byte in it. What the
            # document promises is "something on stderr saying so", and a
            # blank line says nothing to the person reading the terminal.
            return (
                f"exit 1 with nothing on stderr saying so ({err!r}): a "
                "failure it did not report"
            )
        head = err.splitlines()[0]
        if REPORT_HEAD.match(head):
            if "\n --> " not in err:
                return f"exit 1, but the report carries no position: {err!r}"
        elif " --> " in err:
            return (
                f"exit 1 with a position under {head!r}, which names no kind "
                f"of error: {err!r}"
            )
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


def printable(argv):
    """The command line as a reader would type it, short enough to read.

    One of these is five thousand brackets. A counterexample is the whole of
    the evidence, so it is quoted verbatim wherever it can be -- but a wall
    nobody can see past is not evidence either, and the two that would be a
    wall say how much of them is missing.
    """
    text = "vine " + " ".join(shlex.quote(a) for a in argv)
    if len(text) > 120:
        text = f"{text[:100]}... and {len(text) - 100} more characters"
    return text


def check():
    """Returns (how many command lines were checked, the ones that broke it)."""
    failures = []
    checked = 0
    seen = set()
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
            shown = printable(argv)
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
                failures.append((shown, f"did not finish in {TIMEOUT}s"))
                continue
            seen.add(done.returncode)
            broke = broken_by(argv, done)
            if broke is not None:
                failures.append((shown, broke))
        os.chmod(noread, 0o600)

    checked += 1
    promised = documented_statuses()
    if promised is None:
        failures.append((
            str(SPEC),
            f"has no one paragraph starting {PARAGRAPH!r} -- the endings are "
            "promised somewhere this cannot find, so nothing was compared",
        ))
    elif promised != seen:
        failures.append((
            str(SPEC),
            f"promises the endings {sorted(promised)} and these command lines "
            f"produced {sorted(seen)}",
        ))
    return checked, failures
