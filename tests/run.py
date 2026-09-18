#!/usr/bin/env python3
"""Golden-file test runner. No dependencies, no network, no test framework.

Each case is a `.vine` file under tests/cases with a sibling expectation:

  foo.vine + foo.out   the program runs; its stdout must match foo.out exactly
  foo.vine + foo.err   the program must fail; the rendered error must match

Expectations are written by hand on purpose. There is deliberately no flag to
regenerate them from actual output: a golden file that can rewrite itself to
match a regression is not a test.
"""

import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vine import Source, run  # noqa: E402
from vine.errors import VineError  # noqa: E402

CASES = ROOT / "tests" / "cases"
GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def expectation_for(case):
    for suffix in (".out", ".err"):
        candidate = case.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


def actual_for(case):
    """Returns (kind, text) where kind is 'out' or 'err'."""
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
    cases = sorted(CASES.rglob("*.vine"))
    if only:
        cases = [c for c in cases if only in str(c)]
    if not cases:
        print("no cases found")
        return 1

    failures = []
    for case in cases:
        name = str(case.relative_to(CASES))
        expected_file = expectation_for(case)
        if expected_file is None:
            failures.append((name, "no .out or .err expectation file"))
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
