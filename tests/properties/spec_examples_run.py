"""Every example in docs/spec.md runs, and answers what it claims.

The document holds sixty-odd `expression    # result` lines and nothing ran a
single one of them until this file existed. They read to a reviewer as
evidence -- an expression next to its answer, in the tone of a transcript --
and they were a hand-written expectation stored where the test runner never
looks. Tick 19 ran all of them and every one was true, which is the result
that makes this property worth having rather than the one that makes it
unnecessary: the claims are right today, so a check added now records that and
fails the day one stops being.

This does not make the goldens redundant, and it is not the collapse tick 13
warned about. A delegation makes two answers one; here the spec's comment and
the golden under `tests/cases/` are two expectations, each written by hand and
each compared against the implementation, never against each other. What they
catch differs: a golden catches the implementation drifting, and this catches
the *document* drifting -- an example edited into a falsehood, which no golden
can see, because no golden reads the document.

## Two kinds of claim

An untagged fenced block is Vine; a tagged one is not, which is how the
**Running it** block (```sh) stays out. A block's lines are fed to one
interpreter in order, so a `let` binds for the lines under it, exactly as the
REPL binds across entries. Entries that span lines are joined by the parser's
own "ran out of input" flag, which is the rule `vine/repl.py` uses and not a
second guess at it.

**A result comment** is the text after `#` on an entry's last line, up to the
first em dash; the rest is commentary. One beginning `error:` (or `runtime
error:` / `syntax error:`) claims the entry fails with that message, compared
against the first line of the rendered error -- the bare `error:` matching
either kind, since the document uses it as a shorthand in two places and the
distinction is **Errors**' subject, not the example's.

One beginning `refused:` claims the entry ends the program with that message
instead. A refusal is not an error and has no rendered report to read a first
line out of -- see **Refusing** -- so it needs its own notation, and it needs
one at all because the alternative is a `fail` in an untagged block ending
this property in a Python traceback.

Any other result is compared against three *exact* observables of the run:
what the entry printed, the value's `str`, and the value's `repr`. It passes
if it equals one of them. That tolerance is about the document's notation and
not about the answer: for every value but a top-level string, `str` and `repr`
agree, and for a string the spec writes the text in the sections that are
about text (**repr and str**, **Map order**) and the source everywhere else.
Both are true statements about the same run. The one entry that both prints
and answers -- `tap([1, 2]) |> take(1)` -- could therefore pass by matching
the wrong observable; its printed half is pinned by `tests/cases/printing.vine`.

**A report block** (```report) is a whole rendered failure, compared line for
line against the program in the untagged block *immediately above it*. Fifteen
of them, in seven sections, and until tick 32 not one was compared past its
headline: a result comment cannot hold a caret, so every note and every help
the document printed sat outside every check in the repository. Four blocks
were being fed to the interpreter as if they were programs, where they failed
to parse and were discarded in silence.

A report says which source it is about on its ` --> ` line, and that name
chooses how the program is run. `<repl:N>` is a session: the lines are typed
at `vine/repl.py` and the report is what it wrote after the last of them, so
the entry number in that name is the implementation's and is checked. Any
other name is a file, and there the name is the document's own -- `report.vine`
is a stand-in for whatever the reader calls their file, so it is handed to the
runner rather than checked. Nothing else in a report is the document's: the
position, the quoted line, the caret column and every extra line come from the
run.

A whole report is the only form. An excerpt -- a headline alone, or the note
lines without the caret above them -- reads as a transcript and is checked by
nothing, so an untagged block whose first line is an error headline, or which
carries a ` = note: ` or ` = help: ` line, fails this property as a report
that lost its tag. Three blocks in **Early return** and two in **Errors** were
excerpts before tick 32 made them whole; the two in **Errors** were the note
lines of `call_chain_deep` and `infinite_recursion`, whose programs the reader
could not see, so `d was called at 6:18` named a line that was nowhere in the
document.

Reading the wrong *number* of either kind is a failure, for the reason
`roster_names_every_builtin.py` gives: a property that reads the document has
to fail when the document changes shape, or it quietly stops checking.
"""

import io
import pathlib
import re

from vine import run
from vine.errors import Source, SyntaxError_, VineError
from vine.interp import FailSignal, Interpreter
from vine.parser import parse
from vine.repl import CONTINUE, PROMPT, Repl
from vine.values import to_display, to_repr

CLAIM = (
    "every 'expression # result' line in a Vine block of docs/spec.md runs "
    "and answers exactly the result its comment claims, and every report "
    "block is exactly what the program above it prints when it fails"
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
EXPECTED = 128
# The same claim for report blocks, and it is the tighter of the two: a report
# that loses its tag stops being read and starts being parsed as a program.
REPORTS = 19

REPORT = "report"
HEADLINE = re.compile(r"^(syntax error|runtime error|error): ")
ARROW = re.compile(r"^ *--> (.+):(\d+):(\d+)$")
EXTRA = re.compile(r"^ *= (note|help): ")


def blocks():
    """Every fenced block, as (tag, lines)."""
    found, body, inside, tag = [], [], False, ""
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            if inside:
                found.append((tag, body))
                body, inside = [], False
            else:
                inside, tag = True, line[3:].strip()
            continue
        if inside:
            body.append(line)
    return found


def vine_blocks():
    """The untagged fenced blocks, as lists of lines."""
    return [body for tag, body in blocks() if not tag]


def report_blocks():
    """Each report block with the untagged block above it, as (program, want)."""
    pairs, program = [], None
    for tag, body in blocks():
        if tag == REPORT:
            pairs.append((program, body))
        elif not tag:
            program = body
    return pairs


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


def file_report(lines, name):
    """What running these lines as a file called `name` reports, or None."""
    try:
        run("\n".join(lines) + "\n", name, out=io.StringIO())
    except VineError as exc:
        return exc.render()
    except FailSignal as signal:
        # A refusal has no report, so it cannot match one. Returned rather
        # than raised so that a `fail` written above a report block fails this
        # property with its own text quoted, instead of ending the suite.
        return signal.text
    return None


def session_report(lines):
    """What the REPL wrote after the last of these lines was typed, or None.

    Read out of the session's own transcript rather than rebuilt: the entry
    numbers in `<repl:N>` are what this claim is about, and a second guess at
    how the REPL names its sources would agree with itself.
    """
    transcript = io.StringIO()
    Repl(io.StringIO("\n".join(lines) + "\n"), transcript, interactive=False,
         err=transcript).run()
    written = transcript.getvalue().splitlines()
    prompts = (PROMPT.rstrip(), CONTINUE.rstrip())
    typed = [i for i, line in enumerate(written) if line.startswith(prompts)]
    after = written[typed[-1] + 1:] if typed else written
    return "\n".join(after) if after else None


def check_reports(failures):
    """Every report block, against the program in the block above it."""
    checked = 0
    for program, want in report_blocks():
        checked += 1
        text = "\n".join(want)
        if program is None:
            failures.append((text, "has no program block above it to run"))
            continue
        arrow = ARROW.match(want[1]) if len(want) > 1 else None
        if arrow is None:
            failures.append((text, "has no ' --> name:line:col' line to say what it is about"))
            continue
        name = arrow.group(1)
        got = (
            session_report(program)
            if name.startswith("<repl:")
            else file_report(program, name)
        )
        if got is None:
            failures.append(("\n".join(program), f"claims a report and did not fail:\n{text}"))
        elif got != text:
            failures.append(("\n".join(program), f"reports\n{got}\nand the document says\n{text}"))
    if checked != REPORTS:
        failures.append(
            (
                str(SPEC),
                f"read {checked} report blocks and expected exactly {REPORTS}. "
                "If you added or removed one, update REPORTS in the same commit.",
            )
        )
    return checked


def check_untagged(failures):
    """An untagged block that is really a report has stopped being checked."""
    for body in vine_blocks():
        if not body:
            continue
        line = next((l for l in body if EXTRA.match(l)), None)
        if HEADLINE.match(body[0]):
            line = body[0]
        if line is not None:
            failures.append(
                ("\n".join(body), f"is a report and is not tagged ```{REPORT}: {line!r}")
            )


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
                failed = refused = None
            except VineError as exc:
                value, failed, refused = None, exc.render().split("\n")[0], None
            except FailSignal as signal:
                value, failed, refused = None, None, signal.text
            if want is None:
                continue
            checked += 1
            wants_refusal = want.startswith("refused:")
            if wants_refusal or refused is not None:
                if refused is None:
                    failures.append((text, f"claims {want!r} and did not refuse"))
                elif not wants_refusal:
                    failures.append((text, f"claims {want!r} and refused with {refused!r}"))
                elif refused != want[len("refused:"):].strip():
                    failures.append((text, f"claims {want!r} and refused with {refused!r}"))
                continue
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
    check_untagged(failures)
    return checked + check_reports(failures), failures
