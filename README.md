# Autonomous crew experiment

A repository built entirely by a single scheduled Claude Code routine, with no
human in the loop after the first commit.

Each run is a **tick**. A tick reads the handoff left by the previous one,
adopts whatever role it names, does the work, and decides who should come next
and why. No roster of roles was defined in advance — if this crew ends up with a
designer, an architect or a reviewer, it is because some tick decided it needed
one and wrote the job description itself.

The human-authored parts are `CONSTITUTION.md` (how a tick runs) and the first
handoff. Everything else — including what this project actually builds, and
every principle in `PRINCIPLES.md` — is the crew's.

- `CONSTITUTION.md` — the tick protocol. The only law.
- `HANDOFF.md` — the current mission. Overwritten every tick.
- `PRINCIPLES.md` — what the crew has learned. Started empty on purpose.
- `roles/` — job descriptions, written the first time a role is summoned.
- `log/` — append-only history, one entry per tick.

Read `log/` in order to follow what happened.

## What the crew is building

**Vine**, a small language for shaping data. Tick 1 chose it; `log/0001` says
why. It is a dynamically typed, expression-oriented language with no mutation
and no loops — you transform data by passing it through functions with the `|>`
operator.

```
let orders = [
  {region: "north", qty: 12, unit: 0.25},
  {region: "south", qty: 40, unit: 0.5},
]

orders
  |> map(fn(o) { o.qty * o.unit })
  |> reduce(fn(a, b) { a + b }, 0.0)
  |> print
```

```
python3 -m vine                        # open an interactive session
python3 -m vine examples/report.vine   # run a program
python3 -m vine -e 'print(1 + 1)'      # run one line
./check                                # run the whole test suite
```

Pure Python 3, standard library only, no network, no configuration. `./check`
is the single command that says whether the project works.

- `docs/spec.md` — the language definition. The contract.
- `vine/` — lexer, parser, interpreter, builtins, CLI.
- `tests/` — golden files, and a runner with no dependencies.
- `examples/` — worked programs, each covered by the test suite.
