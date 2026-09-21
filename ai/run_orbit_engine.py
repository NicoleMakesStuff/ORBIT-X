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
    parser = argparse.ArgumentParser(
        description="Run ORBIT-X orbit propagation and telemetry"
    )

    parser.add_argument(
        "--satellite-id",
        type=int,
        action="append",
        dest="satellite_ids"
    )

    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=0
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None
    )

    return parser.parse_args()


def main() -> None:

    # --------------------------------------------------
    # Locate project root
    # --------------------------------------------------

    project_root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )

    # --------------------------------------------------
    # Load backend/.env explicitly
    # --------------------------------------------------

    env_path = os.path.join(
        project_root,
        "backend",
        ".env"
    )

    print(f"Loading environment from: {env_path}")

    load_dotenv(
        dotenv_path=env_path,
        override=True
    )

    # --------------------------------------------------
    # Read MongoDB configuration
    # --------------------------------------------------

    uri = os.getenv("MONGODB_URI")

    if not uri:
        raise RuntimeError(
            f"MONGODB_URI is not configured in {env_path}"
        )

    database_name = os.getenv(
        "MONGODB_DB_NAME",
        "orbit_x"
    )

    args = parse_args()

    # --------------------------------------------------
    # Connect to MongoDB
    # --------------------------------------------------

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")

    print("[SUCCESS] MongoDB connection successful")

    database = client[database_name]

    try:

        # --------------------------------------------------
        # Run orbit engine
        # --------------------------------------------------

        while True:

            counts = run_once(
                database,
                args.satellite_ids,
                datetime.now(timezone.utc),
                args.seed
            )

            print(
                f"Orbit cycle complete: {counts}"
            )

            # Run only once unless an interval was requested.
            if args.interval_seconds <= 0:
                break

            time.sleep(
                args.interval_seconds
            )

    finally:

        client.close()

        print("[INFO] MongoDB connection closed")


if __name__ == "__main__":
    main()