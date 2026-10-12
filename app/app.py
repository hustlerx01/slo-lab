"""Sample 'checkout' service with Prometheus metrics and a chaos knob.
GET /checkout      -> 200 or 500 (chaos), latency ~N(40ms) (+ chaos latency)
POST /chaos?error_rate=0.3&latency_ms=0   -> set fault injection (lab only)
GET /metrics
"""
import os, random, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQS = Counter("http_requests_total", "Requests", ["route", "code"])
LAT = Histogram("http_request_duration_seconds", "Latency", ["route"],
                buckets=(0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 2.5))
STATE = {"error_rate": float(os.environ.get("ERROR_RATE", "0")), "latency_ms": float(os.environ.get("LATENCY_MS", "0"))}
LOCK = threading.Lock()

def handle_checkout():
    with LOCK: er, extra = STATE["error_rate"], STATE["latency_ms"]
    d = max(0.005, random.gauss(0.04, 0.01)) + extra / 1000
    time.sleep(d)
    code = 500 if random.random() < er else 200
    REQS.labels("/checkout", str(code)).inc(); LAT.labels("/checkout").observe(d)
    return code

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body=b"", ctype="text/plain"):
        self.send_response(code); self.send_header("Content-Type", ctype); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/metrics": return self._send(200, generate_latest(), CONTENT_TYPE_LATEST)
        if p == "/checkout": c = handle_checkout(); return self._send(c, b"ok\n" if c == 200 else b"error\n")
        if p == "/healthz": return self._send(200, b"ok\n")
        self._send(404)
    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/chaos": return self._send(404)
        q = parse_qs(u.query)
        with LOCK:
            for k in ("error_rate", "latency_ms"):
                if k in q: STATE[k] = float(q[k][0])
            body = repr(STATE).encode()
        self._send(200, body)

def serve(port=8000):
    s = ThreadingHTTPServer(("0.0.0.0", port), H); s.serve_forever()

if __name__ == "__main__":
    serve(int(os.environ.get("PORT", "8000")))
