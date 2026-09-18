#!/usr/bin/env python3
"""Drive the REPL on a real pty and send it real Ctrl-C signals.

    python3 tests/manual/pty_interrupt.py

This is deliberately NOT part of ./check. It depends on sleeps to let the
child reach its prompt, and a suite that can fail because a machine was busy
teaches the crew to ignore failures. What it covers instead is the one thing
the golden case tests/cases/repl/interrupt.repl cannot: that a SIGINT from a
terminal really does surface as a KeyboardInterrupt where the handler is
waiting. The golden proves the handler is right; this proves the signal
arrives.

Run it after touching vine/repl.py, and paste the output into your log entry.
The session below should end with a live prompt and exit status 0 -- once with
an entry half-typed, once with a four-million-element map half-evaluated.
"""

import os
import pty
import select
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(ROOT)
        os.execv(sys.executable, [sys.executable, "-m", "vine"])

    seen = []

    def drain():
        while select.select([fd], [], [], 0.3)[0]:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            seen.append(chunk.decode(errors="replace"))

    def send(keys, settle=0.4):
        time.sleep(settle)
        os.write(fd, keys)
        drain()

    drain()
    send(b"let half = fn(n) {\r")
    send(b"\x03")  # Ctrl-C with an entry half-typed
    send(b"2 + 2\r")
    send(b"range(4000000) |> map(fn(n) { n * 2 }) |> len\r")
    send(b"\x03", settle=1.0)  # Ctrl-C with an entry half-evaluated
    send(b'"alive"\r')
    send(b"\x04")  # Ctrl-D ends the session
    _, status = os.waitpid(pid, 0)

    sys.stdout.write("".join(seen))
    code = os.waitstatus_to_exitcode(status)
    print(f"\n--- exit status: {code}")
    if code != 0 or '"alive"' not in "".join(seen):
        print("--- FAILED: the session did not survive both interrupts")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
