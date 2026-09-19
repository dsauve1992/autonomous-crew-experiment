"""Every `expression    # result` line in docs/spec.md answers what it claims.

The document holds sixty-odd of these and nothing ran a single one of them
until this file existed. They read to a reviewer as evidence -- an expression
next to its answer, in the tone of a transcript -- and they were a
hand-written expectation stored where the test runner never looks. Tick 19
ran all of them and every one was true, which is the result that makes this
property worth having rather than the one that makes it unnecessary: the
claims are right today, so a check added now records that and fails the day
one stops being.

This does not make the goldens redundant, and it is not the collapse tick 13
warned about. A delegation makes two answers one; here the spec's comment and
the golden under `tests/cases/` are two expectations, each written by hand and
each compared against the implementation, never against each other. What they
catch differs: a golden catches the implementation drifting, and this catches
the *document* drifting -- an example edited into a falsehood, which no golden
can see, because no golden reads the document.

## What counts as a claim, and how it is compared

An untagged fenced block is Vine; a tagged one (```sh) is not, which is how
the **Running it** block stays out. A block's lines are fed to one
interpreter in order, so a `let` binds for the lines under it, exactly as the
REPL binds across entries. Entries that span lines are joined by the parser's
own "ran out of input" flag, which is the rule `vine/repl.py` uses and not a
second guess at it.

The result is the comment text up to the first em dash; the rest is
commentary. A result beginning `error:` (or `runtime error:` / `syntax
error:`) claims the entry fails with that message, compared against the first
line of the rendered error -- the bare `error:` matching either kind, since
the document uses it as a shorthand in two places and the distinction is
**Errors**' subject, not the example's.

Any other result is compared against three *exact* observables of the run:
what the entry printed, the value's `str`, and the value's `repr`. It passes
if it equals one of them. That tolerance is about the document's notation and
not about the answer: for every value but a top-level string, `str` and `repr`
agree, and for a string the spec writes the text in the sections that are
about text (**repr and str**, **Map order**) and the source everywhere else.
Both are true statements about the same run. The one entry that both prints
and answers -- `tap([1, 2]) |> take(1)` -- could therefore pass by matching
the wrong observable; its printed half is pinned by `tests/cases/printing.vine`.

Reading the wrong *number* of claims is a failure, for the reason
`roster_names_every_builtin.py` gives: a property that reads the document has
to fail when the document changes shape, or it quietly stops checking.
"""

import io
import pathlib
import re

from vine.errors import Source, SyntaxError_, VineError
from vine.interp import Interpreter
from vine.parser import parse
from vine.values import to_display, to_repr

CLAIM = (
    "every 'expression # result' line in a Vine block of docs/spec.md runs, "
    "and answers exactly the result its comment claims"
)

SPEC = pathlib.Path(__file__).resolve().parent.parent.parent / "docs" / "spec.md"
# A result comment: something, whitespace, '#', something. The whitespace is
# what separates it from a line that is only a comment.
RESULT = re.compile(r"\S\s+#\s*(\S.*)$")
# How many the document holds. Exact, not a floor: tick 19 wrote this as "at
# least 60" and then tagged one block `vine` to see what would happen. Two
# claims stopped being checked, the count fell to 65, and the property passed
# -- a guard that sleeps through the failure it was put there for. Partial
# blindness is the realistic way a document-reading check goes wrong, and only
# an exact number sees it. A tick that adds or removes an example edits this
# line in the same commit, which is the point: the count is a claim too.
EXPECTED = 96


def vine_blocks():
    """The untagged fenced blocks, as lists of lines."""
    blocks, body, inside, tagged = [], [], False, False
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            if inside:
                if not tagged:
                    blocks.append(body)
                body, inside = [], False
            else:
                inside, tagged = True, bool(line[3:].strip())
            continue
        if inside:
            body.append(line)
    return blocks


def entries(lines):
    """Group lines into entries the way the REPL does: keep reading while the
    parser says it ran out of input rather than found the wrong thing."""
    grouped, buffer = [], []
    for line in lines:
        if not line.strip() and not buffer:
            continue
        buffer.append(line)
        source = Source("\n".join(buffer), "<spec>")
        try:
            parse(source)
        except SyntaxError_ as exc:
            if exc.at_eof:
                continue
        grouped.append(buffer)
        buffer = []
    if buffer:
        grouped.append(buffer)
    return grouped


def claimed(entry):
    """The result the entry's last line claims, or None."""
    match = RESULT.search(entry[-1])
    if not match:
        return None
    return match.group(1).split("—")[0].strip()


def check():
    checked, failures = 0, []
    for lines in vine_blocks():
        interp = Interpreter(Source("", "<spec>"), io.StringIO())
        for entry in entries(lines):
            text = "\n".join(entry)
            want = claimed(entry)
            printed = io.StringIO()
            interp.out = printed
            try:
                source = Source(text, "<spec>")
                value = Interpreter.run(interp, parse(source), source)
                failed = None
            except VineError as exc:
                value, failed = None, exc.render().split("\n")[0]
            if want is None:
                continue
            checked += 1
            wants_error = want.startswith(("error:", "runtime error:", "syntax error:"))
            if wants_error:
                kinds = ["runtime error:", "syntax error:"]
                allowed = [want] + [
                    want.replace("error:", kind, 1) for kind in kinds
                ] if want.startswith("error:") else [want]
                if failed is None:
                    failures.append((text, f"claims {want!r} and did not fail"))
                elif failed not in allowed:
                    failures.append((text, f"claims {want!r} and failed with {failed!r}"))
                continue
            if failed is not None:
                failures.append((text, f"claims {want!r} and failed with {failed!r}"))
                continue
            seen = [printed.getvalue().rstrip("\n")]
            seen += ["nil"] if value is None else [to_display(value), to_repr(value)]
            if want not in seen:
                failures.append((text, f"claims {want!r} and the run gives {seen!r}"))
    if checked != EXPECTED:
        failures.append(
            (
                str(SPEC),
                f"read {checked} result comments and expected exactly {EXPECTED}. "
                "If you added or removed an example, update EXPECTED in the same "
                "commit; otherwise a block has changed shape and claims are no "
                "longer being read.",
            )
        )
    return checked, failures
