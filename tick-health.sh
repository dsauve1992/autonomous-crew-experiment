#!/usr/bin/env sh
# Mechanical snapshot of repo state. Ticks paste the output into their log entry
# so drift is measurable rather than self-reported.
echo "commits:    $(git rev-list --count HEAD 2>/dev/null || echo 0)"
echo "ticks:      $(ls log/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "roles:      $(ls roles/*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "files:      $(git ls-files | wc -l | tr -d ' ')"
echo "lines:      $(git ls-files | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')"
echo "principles: $(grep -c '^' PRINCIPLES.md 2>/dev/null || echo 0) lines"
