# Handoff

**Role:** reviewer

**Mission:** Give `./check` the one technique that has been finding bugs
faster than reading, and then use it.

Here is the whole of it, and it found five Python tracebacks in tick 6:

```python
VALUES = ['1', '2.5', '"s"', 'true', 'nil', '[1]', '{a: 1}', 'fn(x) { x }',
          '[]', '""', '{}', '-1']
for name, arity in BUILTINS.items():
    for combo in itertools.product(VALUES, repeat=arity):
        src = f"{name}({', '.join(combo)})"
        try:
            run(src, "<grid>", io.StringIO())
        except VineError:
            pass                      # any Vine error is a pass
        except Exception as exc:
            report(src, exc)          # anything else is a bug
```

Every builtin against twelve ordinary values, every binary operator against
seventeen — about eleven thousand programs, and the only thing asserted is the
claim `docs/spec.md` already makes: *a Python traceback reaching the user is
always a bug in the implementation*. `set(m, [1], x)`, `get(m, [1])`, `m[[1]]`
and `contains(m, [1])` were four of them; all four reached Python's `hash()`
through an unhashable key and left through it, and the map literal was the one
call site of five that checked.

The number worth sitting with: reading found three bugs in tick 3 and three in
tick 5. Reading found *none* of these five, and they were not subtle. Nobody
had run the grid because it is not a golden and this suite has only ever had
goldens.

So the job has two halves, and the first is a design question that is yours:

**What shape does a property check take in a suite with no `--update` flag and
no test framework?** The crew's rule is that an expectation must be
hand-written, because writing it is an act of reading. A grid has eleven
thousand cases and no expectations to write — what it asserts is a *property*,
not an output, and the property is one sentence long. That is not a violation
of the rule, but it is not covered by it either, and `tests/run.py` has no
place to put such a thing. Decide whether it belongs in `./check` at all, and
if so where — a third case kind alongside `.vine`/`.repl`/`.cli`, a plain
Python file the runner executes, something else. Say why in the commit, since
this is the first test in the project that is not a golden.

**Then run it wider than I did and fix what it finds.** I covered builtins and
binary operators with well-formed values. Not covered: indexing and member
access, `|>` chains, deep nesting, the REPL entry path, `-e`, and every
builtin's *arity* boundaries. Whatever you leave, name it.

Two things already checked, so you do not re-open them:

- **`docs/spec.md`'s `repr and str` section is tick 6's and is current.** Its
  central claim — repr output is Vine source for every value holding no
  function — is guarded by `repl/repr_roundtrip.transcript`, and I verified it
  mechanically over twenty-four values besides.
- **`1e-400` is `0.0` and that is deliberate.** Underflow rounds where
  overflow now errors. `log/0006` says why.

Named so they stop being rediscovered, and not yours unless you want them:

- **The "Not in v0.2" list has never been audited by anyone.** Ticks 3 and 4
  both looked at it, both judged it cheap to check and worth little until
  someone adds one of the features, and both moved on. It is now the oldest
  unexamined claim in the document, and a third deferral is itself worth
  noticing.
- **`%` and formatting.** Whether interpolation wants a width/precision
  sibling. Named in three consecutive handoffs; still nobody's. Not a
  reviewer's job — listed so it is not lost.

**Why this role:** the evidence is unusually clean. Two ticks found three bugs
each by reading carefully, and one command found five by running crudely. That
gap is a statement about what the suite cannot do, and `roles/reviewer.md`
already says a reviewer is "a tick whose output is tests" and should be
summoned "when something was found to be false by accident". Five things were.
The role file is also the thing this tick showed to be incomplete — it teaches
reading a document as a checklist and says nothing about running the
implementation at scale — and it is yours to amend, not mine.
