"""The chain the experiment runs on says the same thing in all three places.

`CONSTITUTION.md` names one failure that can end this experiment quietly: *"A
broken handoff is the one failure that can kill this experiment silently."*
Everything else here is held by something. The chain itself was held by
nobody, and it has been wrong once.

Tick 41 wrote its log entry and `HANDOFF.md` in one commit. The log's
**Handoff** section says `vine-programmer`; `HANDOFF.md` says `reviewer`. The
tick that arrived read `HANDOFF.md`, as the protocol says to, so nothing broke
-- but `log/` is append-only, so the record is wrong for good and cannot be
corrected. Anyone reconstructing the chain from the log alone gets tick 42
wrong.

This is not about Vine programs, which is what a property here usually is
about. It lives here because `./check` is the one thing every tick runs, and a
check nobody runs is a note.

Four clauses.

1. **`HANDOFF.md` names one role and one mission**, in the shape the
   constitution gives, and the role is one the crew has a file for. A handoff
   whose role line has gone missing is the incoherent handoff the constitution
   has a recovery procedure for, and this is what notices before a tick has to.
2. **The newest log entry hands off to the role `HANDOFF.md` names.** These
   two are written minutes apart by one author and are the pair that has to
   agree; the failure above is a tick changing its mind about the role and
   updating one of them. Read as the *first* role named in the entry's
   **Handoff** section, because that is how all forty-two are written -- the
   role, then the reasoning, which usually names other roles to rule them out.
3. **Every past link agrees with the tick that followed it**, with tick 41
   pinned as the one that does not. Pinned from both sides, the way
   `composition_holds.py` pins `replace`'s empty needle: the clause fails if a
   second break appears, and it fails if tick 41 stops being a break, because
   the only way that happens is somebody editing an append-only file.
4. **The log is a run of ticks with no gaps**, `0001` upward, and each file's
   `# Tick <n> -- <role>` headline agrees with its own name. A gap is a tick
   whose entry never landed; a headline that disagrees with the file name is
   the same mismatch as clause 2, one layer down.

What none of this can check is whether the role was the *right* one. That is
the judgement the experiment exists to observe, and it is not a thing a file
can hold.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LOG = ROOT / "log"
ROLES = ROOT / "roles"
HANDOFF = ROOT / "HANDOFF.md"

CLAIM = (
    "HANDOFF.md names one role the crew has a file for, the newest log entry "
    "hands off to that same role, every earlier entry hands off to the role "
    "of the tick that followed it, and the log is a gapless run of ticks whose "
    "headlines match their file names"
)

ROLE_LINE = re.compile(r"^\*\*Role:\*\*\s*(\S+)\s*$", re.MULTILINE)
MISSION_LINE = re.compile(r"^\*\*Mission:\*\*", re.MULTILINE)
HEADLINE = re.compile(r"^# Tick (\d+) [-—]+ (\S+)\s*$")
ENTRY = re.compile(r"^(\d{4})-(.+)\.md$")

# The one link in the chain whose two records disagree, and cannot stop
# disagreeing: `log/` is append-only. Written as the number rather than as a
# rule so that a second one is a failure and not a second exception.
KNOWN_BREAK = 41


def entries():
    """Every log entry as (tick number, role, text), in order."""
    found = []
    for path in sorted(LOG.glob("*.md")):
        match = ENTRY.match(path.name)
        if match:
            found.append((int(match.group(1)), match.group(2), path))
    return found


def handed_to(text, known):
    """The first role named in an entry's Handoff section, or None."""
    at = text.find("\n## Handoff")
    if at < 0:
        return None
    longest_first = sorted(known, key=len, reverse=True)
    named = re.compile(r"(?<![\w-])(" + "|".join(longest_first) + r")(?![\w-])")
    hit = named.search(text[at:])
    return hit.group(1) if hit else None


def check():
    checked = 0
    failures = []

    known = {p.stem for p in ROLES.glob("*.md")}
    log = entries()

    # 1. HANDOFF.md is in the shape the constitution gives.
    checked += 1
    handoff = HANDOFF.read_text(encoding="utf-8")
    roles_named = ROLE_LINE.findall(handoff)
    if len(roles_named) != 1:
        failures.append((
            "HANDOFF.md",
            f"has {len(roles_named)} '**Role:** <name>' lines and needs exactly "
            "one; a tick cannot read its role out of this",
        ))
    elif roles_named[0] not in known:
        failures.append((
            "HANDOFF.md",
            f"names the role {roles_named[0]!r}, and roles/{roles_named[0]}.md "
            f"does not exist; the crew has {sorted(known)}",
        ))
    if not MISSION_LINE.search(handoff):
        failures.append(("HANDOFF.md", "has no '**Mission:**' line"))

    # 2. The newest entry hands off to that role.
    checked += 1
    if not log:
        failures.append((str(LOG), "holds no log entries"))
    elif len(roles_named) == 1:
        number, _, path = log[-1]
        got = handed_to(path.read_text(encoding="utf-8"), known)
        if got != roles_named[0]:
            failures.append((
                path.name,
                f"hands off to {got!r} where HANDOFF.md names "
                f"{roles_named[0]!r}; these two are written by one tick and "
                "the log cannot be corrected afterwards",
            ))

    # 3. Every earlier link, with the one break pinned from both sides.
    role_of = {number: role for number, role, _ in log}
    for number, _, path in log:
        following = role_of.get(number + 1)
        if following is None:
            continue
        checked += 1
        got = handed_to(path.read_text(encoding="utf-8"), known)
        if number == KNOWN_BREAK:
            if got == following:
                failures.append((
                    path.name,
                    f"now hands off to {following!r}, and tick {KNOWN_BREAK} is "
                    "recorded here as the one link that does not -- log/ is "
                    "append-only, so this entry should not have changed",
                ))
        elif got != following:
            failures.append((
                path.name,
                f"hands off to {got!r} and tick {number + 1} was "
                f"{following!r}: a link the log records wrongly",
            ))

    # 4. A gapless run, each headline agreeing with its own file name.
    for index, (number, role, path) in enumerate(log, start=1):
        checked += 1
        if number != index:
            failures.append((
                path.name,
                f"is entry {index} of the run and is numbered {number}: "
                "a tick's entry never landed, or two share a number",
            ))
        headline = HEADLINE.match(path.read_text(encoding="utf-8").splitlines()[0])
        if headline is None:
            failures.append((path.name, "does not open '# Tick <n> — <role>'"))
        elif (int(headline.group(1)), headline.group(2)) != (number, role):
            failures.append((
                path.name,
                f"opens '# Tick {headline.group(1)} — {headline.group(2)}' and "
                f"is named for tick {number} of {role}",
            ))

    return checked, failures
