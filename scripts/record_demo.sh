#!/usr/bin/env bash
# FactoryProof demo video — synchronized narration + live trace
set -euo pipefail

ROOT=/home/wesley/Desktop/FactoryProof
PORT=8787
DELAY=0.6
ORIGIN="http://127.0.0.1:${PORT}"
VIDEO=/home/wesley/Desktop/FactoryProof/evidence/demo-video.mp4

log() { echo "[$(date +%H:%M:%S)] $*"; }

# ---------- PART 1: daemon + UI ----------
log "PART1 starting..."
pkill -f "factoryproof.server" 2>/dev/null || true; sleep 1
pkill -f "stage-3 app" 2>/dev/null || true; sleep 1
python3 -m factoryproof.server --delay "$DELAY" > /tmp/fp_server.log 2>&1 &
SRV_PID=$!
for i in $(seq 1 20); do
  curl -s "${ORIGIN}/api/health" >/dev/null 2>&1 && { echo "daemon ready"; break; }
  sleep 0.5
done
sleep 3
DISPLAY=:1 firefox --new-window "${ORIGIN}" >/dev/null 2>&1 &
sleep 8

# ---------- PART 2: start ffmpeg capture ----------
log "PART2 starting ffmpeg capture (100s)..."
ffmpeg -y -f x11grab -video_size 1920x1080 -framerate 30 -i :1 \
       -f alsa -i default -ar 48000 -ac 2 \
       -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 160k \
       -t 100 "${VIDEO}" >/tmp/ffmpeg.log 2>&1 &
FFMPEG_PID=$!
sleep 2

# ---------- PART 3: synchronized narration + demo ----------
log "PART3 narration + demo start..."

t=0
narrate() { echo "NARRATE[$(printf '%d' $t)]: $*"; }

# 0:00 — product intro (daemon + UI visible)
sleep 14
narrate "This is FactoryProof, the software factory that proves its work. Four specialist seats: the Case Coordinator scopes work, the Patch Builder implements the approved contract, the Quality Verifier runs public and sealed checks, and the Release Critic challenges the evidence. A human owner controls promotion."
sleep 14

# 0:14 — THE CASE + start demo
sleep 2
narrate "The reference track is Pocketful: a wallet transfer service where money must never be created, destroyed, or spent twice under retries and concurrency, with exact integer-cents accounting. Starting the case now — watch the live trace."
RUN_ID=$(curl -s -X POST "${ORIGIN}/api/run" -H "Content-Type: application/json" -d '{"mode":"offline"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
log "demo run started: $RUN_ID"
sleep 18

# 0:32 — first build BLOCKED (trace shows it live)
sleep 3
narrate "The trace streams live: the Coordinator opens a bounded room, the Builder implements, and the Verifier's sealed acceptance check BLOCKS it — a repeated idempotency key moved money a second time. That failure is the point: the factory is load-bearing."
sleep 12

# 0:45 — revision + approval
sleep 3
narrate "The Builder revises with an explicit idempotency guard. The public and sealed checks go green, the Critic recommends promotion, and the Human Owner approves. As the trace shows, the case ships with the full audit trail preserved."
sleep 12

# 0:57 — approve click if still at gate
S=$(curl -s "${ORIGIN}/api/run" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status'))")
if [ "$S" = "awaiting_human" ]; then
  log "clicking Approve at gate"
  sleep 2
  DISPLAY=:1 xdotool search --name "FactoryProof" 2>/dev/null | head -1 | xargs -r xdotool click 1 330 720 2>/dev/null || true
  curl -s -X POST "${ORIGIN}/api/approve" -H "Content-Type: application/json" -d "{\"run_id\":\"$RUN_ID\"}" >/dev/null
fi
sleep 6

# 1:09 — clean container
narrate "Each stage is a clean, self-contained Docker service. This is stage three: the atomic transfer path with idempotency replay protection and an audit stream. The container makes no network calls."
sleep 10

# 1:19 — evidence package
narrate "The evidence package holds the deterministic local rehearsal, the cover image, and the slide deck. At kickoff it gains the live BAND Desktop room export, the room-and-service video, and the official harness report."
sleep 10

log "PART3 done, waiting for trace to finish..."
# wait for the run to complete if not done
for i in $(seq 1 30); do
  S=$(curl -s "${ORIGIN}/api/run" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status'))" 2>/dev/null)
  [ "$S" = "shipped" ] && break
  sleep 1
done

# ---------- PART 4: driver the demo (live trace printout) ----------
log "PART4 printing the live trace from the dashboard API..."
echo ""
echo "LIVE TRACE — coordinator scopes, builder builds, verifier seals, critic challenges, owner gates:"
echo "  ────────────────────────────────────────────────────────────────────────────"
curl -s --max-time 90 "${ORIGIN}/api/run" | python3 -c "
import sys, json
d = json.load(sys.stdin)
events = d.get('events', [])
last = ''
for e in events:
    msg = e.get('message', '').replace('\n', ' ')
    if msg == last: continue
    actor = e.get('actor', '?').split(' ')[0]
    color = {'success':'\033[0;32m','danger':'\033[0;31m','warning':'\033[0;33m'}.get(e.get('level',''), '')
    last = msg
    print(f'  [{actor:14}] {e.get(\"kind\"):12} [{e.get(\"level\"):9}] -> {msg}')
"
echo "  ────────────────────────────────────────────────────────────────────────────"
echo ""
echo "FINAL METRICS:"
curl -s "${ORIGIN}/api/run" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('  run id      :', d.get('id'))
print('  status      :', d.get('status'))
print('  mode        :', d.get('mode'))
print('  events      :', len(d.get('events', [])))
print('  agents      :', len(d.get('agents', [])))
m = d.get('metrics', {})
print('  patch attempts:', m.get('patch_attempts', '-'))
print('  blocked checks:', m.get('blocked_checks', '-'))
print('  elapsed      :', m.get('elapsed_ms', '-'), 'ms')
"

# ---------- PART 5: stage-3 clean container ----------
log "PART5 stage-3 clean container..."
cd "$ROOT/stage-3"
python3 app.py --host 127.0.0.1 --port 8081 > /tmp/stage3.log 2>&1 &
SPID=$!
sleep 2
echo "  health : $(curl -s http://127.0.0.1:8081/api/health | python3 -m json.tool | tr -d '\n')"
echo "  tests  :"
python3 -m unittest discover -s tests 2>&1 | tail -1
kill $SPID 2>/dev/null || true
cd "$ROOT"

# ---------- PART 6: evidence ----------
sleep 4
log "PART6 evidence package:"
ls -1 evidence/
echo ""

# ---------- PART 7: stop recorder ----------
log "PART7 stopping ffmpeg..."
kill $FFMPEG_PID 2>/dev/null || true
wait $FFMPEG_PID 2>/dev/null || true
pkill -f "factoryproof.server" 2>/dev/null || true
log "video written to $VIDEO"
