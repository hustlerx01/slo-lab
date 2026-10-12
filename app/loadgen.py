import os, sys, time, urllib.request, urllib.error
url = os.environ.get("TARGET", "http://localhost:8000/checkout"); rps = float(os.environ.get("RPS", "20"))
dur = float(sys.argv[1]) if len(sys.argv) > 1 else float("inf"); end = time.time() + dur
while time.time() < end:
    t = time.time()
    try: urllib.request.urlopen(url, timeout=2).read()
    except Exception: pass
    time.sleep(max(0, 1 / rps - (time.time() - t)))
