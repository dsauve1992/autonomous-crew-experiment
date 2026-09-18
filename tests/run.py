#!/usr/bin/env python3
"""Golden-file test runner. No dependencies, no network, no test framework.

Each case is a source file under tests/cases with a sibling expectation:

  foo.vine + foo.out          the program runs; its stdout must match exactly
  foo.vine + foo.err          the program must fail; the rendered error must match
  foo.repl + foo.transcript   the lines of foo.repl are fed to the REPL as if
                              typed; the whole session, prompts included, must
                              match the transcript exactly
  foo.cli + foo.transcript    each line of foo.cli is a `vine` command line,
                              run in a real subprocess; the transcript records
                              stdout, stderr and the exit status of each

Expectations are written by hand on purpose. There is deliberately no flag to
regenerate them from actual output: a golden file that can rewrite itself to
match a regression is not a test.
"""

import io
import pathlib
import shlex
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vine import Source, run  # noqa: E402
from vine.errors import VineError  # noqa: E402
from vine.repl import Repl  # noqa: E402

# Examples are tested too, so the documentation cannot quietly stop working.
ROOTS = [ROOT / "tests" / "cases", ROOT / "examples"]
# Source extension -> the expectation extensions a case of that kind may have.
EXPECTATIONS = {
    ".vine": (".out", ".err"),
    ".repl": (".transcript",),
    ".cli": (".transcript",),
}
GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def expectation_for(case):
    for suffix in EXPECTATIONS[case.suffix]:
        candidate = case.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


class Keyboard:
    """Stands in for a person typing at the REPL.

    Everything is an ordinary line except `^C`, which raises KeyboardInterrupt
    out of readline instead of returning -- what Python does when a real Ctrl-C
    arrives while the REPL waits for input. Piped stdin never delivers SIGINT,
    so without this the Ctrl-C handler cannot be reached from ./check at all.

    What this proves is that the handler does the right thing. What it cannot
    prove is that the signal arrives; that remains hand-verified on a pty, in
    log/0002 and log/0003.
    """

    def __init__(self, text):
        self.lines = text.splitlines(keepends=True)
        self.i = 0

    def readline(self):
        if self.i >= len(self.lines):
            return ""
        line = self.lines[self.i]
        self.i += 1
        if line.rstrip("\n") == "^C":
            raise KeyboardInterrupt
        return line

    def isatty(self):
        return False


def run_cli(case):
    """Run each command line in the case, and record what a terminal saw."""
    chunks = []
    for line in case.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        done = subprocess.run(
            [sys.executable, "-m", "vine", *shlex.split(line)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        chunk = f"$ vine {line}\n" + done.stdout
        if done.stderr:
            chunk += "--- stderr\n" + done.stderr
        chunks.append(chunk + f"exit {done.returncode}\n")
    return "\n".join(chunks)


def actual_for(case):
    """Returns (kind, text) where kind is 'out', 'err' or 'transcript'."""
    if case.suffix == ".cli":
        return "transcript", run_cli(case)
    if case.suffix == ".repl":
        buffer = io.StringIO()
        Repl(Keyboard(case.read_text(encoding="utf-8")), buffer, interactive=False).run()
        return "transcript", buffer.getvalue()
    buffer = io.StringIO()
    try:
        run(case.read_text(encoding="utf-8"), case.name, out=buffer)
    except VineError as exc:
        return "err", exc.render() + "\n"
    return "out", buffer.getvalue()


def diff(expected, actual):
    exp, act = expected.split("\n"), actual.split("\n")
    lines = []
    for i in range(max(len(exp), len(act))):
        e = exp[i] if i < len(exp) else "<missing>"
        a = act[i] if i < len(act) else "<missing>"
        if e != a:
            lines.append(f"      line {i + 1}:")
            lines.append(f"        expected: {e!r}")
            lines.append(f"        actual:   {a!r}")
    return "\n".join(lines)


def main(argv):
    only = argv[0] if argv else None
    cases = sorted(
        c for root in ROOTS for ext in EXPECTATIONS for c in root.rglob("*" + ext)
    )
    if only:
        cases = [c for c in cases if only in str(c)]
    if not cases:
        print("no cases found")
        return 1

    failures = []
    for case in cases:
        name = str(case.relative_to(ROOT))
        expected_file = expectation_for(case)
        if expected_file is None:
            wanted = " or ".join(EXPECTATIONS[case.suffix])
            failures.append((name, f"no {wanted} expectation file"))
            print(f"{RED}MISSING{RESET} {name}")
            continue
        want_kind = expected_file.suffix.lstrip(".")
        expected = expected_file.read_text(encoding="utf-8")
        kind, actual = actual_for(case)
        if kind != want_kind:
            detail = (
                f"      expected the program to {'fail' if want_kind == 'err' else 'succeed'}"
                f", but it {'failed' if kind == 'err' else 'succeeded'}\n"
                f"      actual output:\n{indent(actual)}"
            )
            failures.append((name, detail))
            print(f"{RED}FAIL{RESET}    {name}")
        elif actual != expected:
            failures.append((name, diff(expected, actual)))
            print(f"{RED}FAIL{RESET}    {name}")
        else:
            print(f"{GREEN}ok{RESET}      {name}")

    print()
    if failures:
        for name, detail in failures:
            print(f"{RED}--- {name}{RESET}")
            print(detail)
            print()
        print(f"{RED}{len(failures)} of {len(cases)} failed{RESET}")
        return 1
    print(f"{GREEN}{len(cases)} passed{RESET}")
    return 0


def indent(text):
    return "".join(f"        {line}\n" for line in text.split("\n"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
