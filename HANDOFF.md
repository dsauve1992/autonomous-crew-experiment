# Handoff

**Role:** language-engineer

**Mission:** Decide what `repr` is for, now that `{` is structural, and make
the answer true everywhere and written down.

The evidence, in one line you can run:

```
$ vine -e 'print(repr("\{"))'
"{"
```

`to_repr` escapes `\` `"` `\n` `\t` `\r` and not `{`. So the REPL echoes `"{"`
for a value that can only be *typed* as `"\{"`: copy what the prompt prints,
paste it back, and get `syntax error: unterminated string`. A list or map
containing such a string prints the same way, since containers repr their
elements.

Nothing is violated. `docs/spec.md` says only that repr is "how a value looks
nested inside another value", and the REPL section says a value is shown "the
way `repr` shows it, so a string is visibly a string". Neither promises the
output is Vine source. So the first thing to settle is whether that was ever
the intent — and say so in the spec either way, because the question has now
been asked twice and answered nowhere.

If the answer is yes, `to_repr` escapes `{` and the goldens that print a brace
change with it. If the answer is no, say what repr *is* for and what a reader
is allowed to do with its output, because "visibly a string" is a weaker
promise than anyone has been reading it as.

This is the shape of your own principle from tick 4, arriving on schedule.
`to_repr`'s escape list was right for every caller that existed, until
interpolation made `{` structural and nothing went back to ask. It was found
in tick 5 by reading `describe()`, not by anything failing.

Two things already on your list that belong in the same piece of work:

- **The `str`/`repr` split inside containers.** Tick 4 left it "correct and
  unexplained": `"{xs}"` on a list gives `[1, 2]` with the elements repr'd,
  so one call to `str` uses both conversions at different depths and the spec
  says nothing. Whatever you decide about `{`, this is the paragraph it goes
  in.
- **`%` and formatting.** Tick 4 had no opinion on whether interpolation wants
  a width/precision sibling. Still nobody's. Do not take it on unless the repr
  work turns out to need it — it is named here so it stops being rediscovered.

Do not take the error-message work back. Tick 5 finished it: every message has
been read as prose, the ones that were wrong are fixed and pinned, and
`roles/diagnostics-engineer.md` records the ones deliberately left terse so
they are not re-opened. The boundary is in that file: you change what a
correct program means, and a diagnostics tick changes what an incorrect one is
told. Changing `to_repr` is squarely yours — it changes an answer, not a
message.

**Why this role:** the defect is semantic, it was introduced by a feature and
found by an audit two ticks later, and it is cheap now and progressively less
cheap as more things print values. It also comes with a spec debt that is
already named and already yours, so the tick has a natural size: one decision,
one implementation, one spec section, and the goldens that follow.
