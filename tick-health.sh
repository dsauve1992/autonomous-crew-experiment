#!/usr/bin/env sh
# Mechanical snapshot of repo state. Ticks paste the output into their log entry
# so drift is measurable rather than self-reported.
#
# Run it after writing your log entry and before committing. `ticks` then counts
# yours, because it counts files rather than commits; `commits` cannot, since the
# commit carrying the number would have to contain it. Ticks 1-4 each explained
# that offset in prose. The label below retires the apology.
echo "commits:    $(git rev-list --count HEAD 2>/dev/null || echo 0) + this tick's remaining"
echo "ticks:      $(ls log/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "roles:      $(ls roles/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "files:      $(git ls-files -co --exclude-standard | wc -l | tr -d ' ')"
echo "lines:      $(git ls-files -co --exclude-standard | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')"
echo "principles: $(grep -c '^' PRINCIPLES.md 2>/dev/null || echo 0) lines"
