import pathlib, shutil, subprocess, sys, threading, time, urllib.request, pytest, yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app")); sys.path.insert(0, str(ROOT / "scripts"))
need_promtool = pytest.mark.skipif(not shutil.which("promtool"), reason="promtool missing")

def test_rules_file_is_generated_and_in_sync():
    import gen_rules
    assert (ROOT / "prometheus/slo-rules.yml").read_text() == gen_rules.render()

def test_burn_thresholds_match_sre_workbook():
    rules = yaml.safe_load((ROOT / "prometheus/slo-rules.yml").read_text())
    alerts = {r["alert"]: r for g in rules["groups"] for r in g["rules"] if "alert" in r}
    assert len(alerts) == 8
    assert "> 0.072 and" in alerts["CheckoutSLOAvailabilityBurn1h"]["expr"]   # 14.4 * 0.005
    assert "> 0.03 and" in alerts["CheckoutSLOAvailabilityBurn6h"]["expr"]    # 6 * 0.005
    assert "> 0.144 and" in alerts["CheckoutSLOLatencyBurn1h"]["expr"]        # 14.4 * 0.01
    for a in alerts.values():
        assert a["labels"]["severity"] in {"page", "ticket"} and a["annotations"]["runbook_url"]

@need_promtool
def test_promtool_check_and_unit_tests():
    assert subprocess.run(["promtool", "check", "rules", "slo-rules.yml"], cwd=ROOT / "prometheus").returncode == 0
    p = subprocess.run(["promtool", "test", "rules", "alerts_test.yml"], cwd=ROOT / "prometheus", capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr

@need_promtool
def test_promtool_suite_detects_wrong_threshold(tmp_path):
    """Mutation: if the fast-burn threshold were 0.5 (100x), the outage test must fail."""
    shutil.copy(ROOT / "prometheus/alerts_test.yml", tmp_path)
    (tmp_path / "slo-rules.yml").write_text((ROOT / "prometheus/slo-rules.yml").read_text().replace("> 0.072", "> 0.5"))
    assert subprocess.run(["promtool", "test", "rules", "alerts_test.yml"], cwd=tmp_path, capture_output=True).returncode != 0

def test_dashboard_queries_reference_recorded_series():
    import json
    d = json.loads((ROOT / "grafana/dashboards/checkout-slo.json").read_text())
    exprs = [t["expr"] for p in d["panels"] for t in p["targets"]]
    assert any("slo:checkout_errors:ratio_rate1h" in e for e in exprs) and d["uid"] == "checkout-slo"

def test_app_metrics_and_chaos():
    import app as svc
    from http.server import ThreadingHTTPServer
    s = ThreadingHTTPServer(("127.0.0.1", 0), svc.H); port = s.server_address[1]
    threading.Thread(target=s.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    assert urllib.request.urlopen(base + "/checkout").status == 200
    urllib.request.urlopen(urllib.request.Request(base + "/chaos?error_rate=1", method="POST"))
    with pytest.raises(urllib.error.HTTPError) as e: urllib.request.urlopen(base + "/checkout")
    assert e.value.code == 500
    m = urllib.request.urlopen(base + "/metrics").read().decode()
    assert 'http_requests_total{code="500",route="/checkout"}' in m and "http_request_duration_seconds_bucket" in m
    s.shutdown()
