#!/usr/bin/env bash
# Live chaos demo WITHOUT Docker: app + loadgen + real Prometheus binary on localhost.
# Phase 1 healthy (2 min) -> Phase 2 chaos 30% errors (4 min) -> poll alerts.
set -euo pipefail; cd "$(dirname "$0")/.."
PY=${PY:-python3}; OUT=$(pwd)/results; mkdir -p "$OUT"; W=$(mktemp -d)
sed 's/app:8000/localhost:8000/' prometheus/prometheus.yml > $W/prometheus.yml; cp prometheus/slo-rules.yml $W/
$PY app/app.py & A=$!
prometheus --config.file=$W/prometheus.yml --storage.tsdb.path=$W/data --web.listen-address=:9091 --log.level=warn & P=$!
trap 'kill $A $P ${L:-} 2>/dev/null; rm -rf $W' EXIT
sleep 2; RPS=20 $PY app/loadgen.py & L=$!
q(){ curl -s "localhost:9091/api/v1/query" --data-urlencode "query=$1" | $PY -c "import json,sys;r=json.load(sys.stdin)['data']['result'];print(r[0]['value'][1] if r else 'n/a')"; }
alerts(){ curl -s localhost:9091/api/v1/alerts | $PY -c "import json,sys;print(', '.join(f\"{a['labels']['alertname']}={a['state']}\" for a in json.load(sys.stdin)['data']['alerts']) or 'none')"; }
log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $OUT/live-demo.log; }
: > $OUT/live-demo.log
log "phase 1: healthy, 20 rps"; sleep 120
log "err5m=$(q slo:checkout_errors:ratio_rate5m) alerts: $(alerts)"
log "phase 2: chaos error_rate=0.3"; curl -s -XPOST "localhost:8000/chaos?error_rate=0.3" >/dev/null
for i in $(seq 1 8); do sleep 30; log "t+$((i*30))s err5m=$(q slo:checkout_errors:ratio_rate5m) err1h=$(q slo:checkout_errors:ratio_rate1h) alerts: $(alerts)"; done
log "phase 3: recover"; curl -s -XPOST "localhost:8000/chaos?error_rate=0" >/dev/null
for i in 1 2 3 4 5 6 7 8 9 10; do sleep 30; log "recover t+$((i*30))s err5m=$(q slo:checkout_errors:ratio_rate5m) alerts: $(alerts)"; done
