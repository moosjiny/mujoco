import sys, json, datetime

n = 0
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        m = json.loads(line)
    except Exception:
        continue
    if m.get("event") != "message":
        continue
    n += 1
    ts = datetime.datetime.fromtimestamp(m.get("time", 0)).strftime("%m-%d %H:%M:%S")
    tags = ",".join(m.get("tags", []))
    msg = m.get("message", "")
    suffix = "   (" + tags + ")" if tags else ""
    print("[" + ts + "] " + msg + suffix)
print("-- " + str(n) + " message(s) in last 72h --")
