#!/usr/bin/env bash
# Prints the built CV page (site/cv/index.html) to site/cv/Abdelrahman-Mahmoud-CV.pdf
# using headless Chrome/Chromium. Run after `mkdocs build`.
set -euo pipefail

SITE_DIR="${1:-site}"
OUT="$SITE_DIR/cv/Abdelrahman-Mahmoud-CV.pdf"
PORT="${CV_PORT:-8123}"

CHROME="${CHROME_BIN:-}"
if [ -z "$CHROME" ]; then
  for c in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$c" >/dev/null 2>&1; then CHROME="$c"; break; fi
  done
fi
[ -n "$CHROME" ] || { echo "No Chrome/Chromium found (set CHROME_BIN)." >&2; exit 1; }

python3 -m http.server "$PORT" --directory "$SITE_DIR" >/dev/null 2>&1 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
sleep 1

"$CHROME" --headless=new --no-sandbox --disable-gpu \
  --no-pdf-header-footer --print-to-pdf-no-header \
  --run-all-compositor-stages-before-draw --virtual-time-budget=15000 \
  --print-to-pdf="$OUT" "http://localhost:$PORT/cv/"

echo "CV PDF written to $OUT"
