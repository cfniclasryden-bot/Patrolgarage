#!/usr/bin/env python3
"""
Cron entry point — runs every 5 minutes.
- Always checks refresh queue and processes any pending refreshes.
- Only runs the daily generator if it's the 5am UTC hour and the daily run hasn't happened today.
"""
import os
os.environ["TZ"] = "UTC"
import time
time.tzset()

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY_MARKER = ROOT / "logs" / f"daily_done_{datetime.utcnow().strftime('%Y%m%d')}.flag"

def log(msg):
    print(f"[cron_entry] {datetime.utcnow().isoformat()} {msg}", flush=True)

def main():
    # Always check queue
    log("Checking refresh queue...")
    subprocess.run(["python3", "scripts/check_refresh_queue.py"], cwd=ROOT)

    # Daily run: only between 05:00 and 05:10 UTC, once per day
    now = datetime.utcnow()
    if now.hour == 5 and not TODAY_MARKER.exists():
        log(f"Triggering daily pipeline run ({now.isoformat()})")
        result = subprocess.run(["python3", "scripts/run_pipeline.py"], cwd=ROOT)
        if result.returncode == 0:
            TODAY_MARKER.parent.mkdir(exist_ok=True)
            TODAY_MARKER.write_text("done")
            log("Daily run marker created")
    else:
        log(f"Not daily hour (hour={now.hour}), skipping daily run")

if __name__ == "__main__":
    sys.exit(main())
