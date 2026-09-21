import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
import certifi


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / "backend" / ".env"

load_dotenv(ENV_FILE)


MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "orbit_x")


COLLECTIONS = [
    "satellites",
    "missions",
    "telemetry",
    "orbital_states",
    "ground_stations",
    "communication_events",
    "alerts",
    "tle_history",
    "ingestion_logs"
]


print("=" * 60)
print("ORBIT-X DATABASE HEALTH CHECK")
print("=" * 60)


client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)


try:

    client.admin.command("ping")

    print("[PASS] MongoDB connection")

    db = client[DB_NAME]

    existing_collections = db.list_collection_names()


    print()
    print("COLLECTIONS")
    print("-" * 60)


    for collection_name in COLLECTIONS:

        if collection_name in existing_collections:

            count = db[collection_name].count_documents({})

            print(
                f"[PASS] {collection_name:<25} "
                f"{count} documents"
            )

        else:

            print(
                f"[FAIL] {collection_name:<25} "
                f"missing"
            )


    print()
    print("SATELLITE DATA")
    print("-" * 60)


    satellites = db["satellites"].find(
        {},
        {
            "_id": 0,
            "norad_id": 1,
            "name": 1
        }
    )


    for satellite in satellites:

        print(
            f"[PASS] "
            f"{satellite.get('norad_id')} "
            f"→ "
            f"{satellite.get('name')}"
        )


    print()
    print("=" * 60)
    print("HEALTH CHECK COMPLETE")
    print("=" * 60)


finally:

    client.close()