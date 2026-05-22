#!/usr/bin/env python3
"""
Cron entry point — triggered once daily at 05:00 UTC by Railway schedule.
Railway fires this container on the cronSchedule; no in-process time checks needed.
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def log(msg):
    print(f"[cron_entry] {datetime.now(timezone.utc).isoformat()} {msg}", flush=True)


def run(cmd):
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr, flush=True)
    log(f"Returncode: {result.returncode}")
    return result.returncode


def main():
    log("Daily cron started")

    queue_rc = run(["python3", "scripts/check_refresh_queue.py"])
    log(f"check_refresh_queue returncode={queue_rc}")

    pipeline_rc = run(["python3", "scripts/run_pipeline.py"])
    log(f"run_pipeline returncode={pipeline_rc}")

    return pipeline_rc


if __name__ == "__main__":
    sys.exit(main())
