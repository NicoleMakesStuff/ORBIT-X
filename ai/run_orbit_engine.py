"""Run the Mongo-backed ORBIT-X orbit and telemetry engine."""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

from orbit.engine import run_once


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ORBIT-X orbit propagation and telemetry")
    parser.add_argument("--satellite-id", type=int, action="append", dest="satellite_ids")
    parser.add_argument("--interval-seconds", type=int, default=0)
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not configured")
    database_name = os.getenv("MONGODB_DB_NAME", "orbit_x")
    args = parse_args()

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    database = client[database_name]
    try:
        while True:
            counts = run_once(database, args.satellite_ids, datetime.now(timezone.utc), args.seed)
            print(f"Orbit cycle complete: {counts}")
            if args.interval_seconds <= 0:
                break
            time.sleep(args.interval_seconds)
    finally:
        client.close()


if __name__ == "__main__":
    main()