# NOTES
- 2026-10-11: promtool 6 scenarios green. Live run: page fired ~3 min after chaos and resolved ~4 min after recovery.
- Bug: the ratio is absent when there are no 5xx series, fixed with `or vector(0)`. Lesson: test the "healthy and boring" path too.
- Burn-rate math to explain: budget 0.5%; 14.4x for 1h = 14.4/720h·1h = 2% of the 30d budget. 6x for 6h = 5%. 3x for 1d = 10%. 1x for 3d = 10%.
- Interview angles: why two windows (long = significance, short = fast reset), SLI choice (server-side vs synthetic), page vs ticket, error-budget policy.
- Next: run compose + screenshot Grafana, add OTel tracing, compare with Sloth output.
