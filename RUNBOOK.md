# Checkout SLO runbook
## availability
1. Open Grafana "Checkout SLO" and check which window is burning. 5m+1h means acute, 6h+30m means sustained.
2. Check recent deploys and roll back if a deploy lines up with the onset.
3. Check dependencies (DB, payment API) error rates. In the lab, check `POST /chaos` state.
4. If the burn continues for more than 30 min, declare an incident and freeze feature deploys until the budget recovers.
## latency
1. Compare p99 against the 300 ms threshold. Check saturation (CPU, connection pools).
2. Scale out or shed load. Roll back if a deploy caused it.
