import os
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

from celestrak import get_tle
from tle_validator import validate_complete_tle, check_tle_age
from tle_updater import compare_tle_epochs, save_tle_history


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / "backend" / ".env"

load_dotenv(ENV_FILE)


MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "orbit_x")


SATELLITES = [
    25544,
    20580,
    33591
]


if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI was not found in backend/.env"
    )


print("=" * 60)
print("ORBIT-X SATELLITE INGESTION")
print("=" * 60)

print(f"Environment file: {ENV_FILE}")
print(f"Database: {DB_NAME}")
print(f"Satellites to ingest: {len(SATELLITES)}")
print()


def ingest_satellite(
    satellites_collection,
    history_collection,
    norad_id
):

    print("-" * 60)
    print(f"[INFO] Processing NORAD {norad_id}")

    # --------------------------------------------------
    # STEP 1 — FETCH TLE
    # --------------------------------------------------

    try:

        print("[INFO] Fetching TLE from CelesTrak...")

        tle = get_tle(norad_id)

        print(
            f"[INFO] Received TLE for {tle['name']}"
        )

    except Exception as error:

        print(
            f"[ERROR] Failed to fetch NORAD {norad_id}"
        )

        print(f"[ERROR] {error}")

        return {
            "norad_id": norad_id,
            "status": "FAILED",
            "error": str(error)
        }


    # --------------------------------------------------
    # STEP 2 — VALIDATE TLE
    # --------------------------------------------------

    validation = validate_complete_tle(
        norad_id,
        tle["name"],
        tle["line1"],
        tle["line2"]
    )


    if not validation["valid"]:

        print(
            f"[ERROR] TLE validation failed for NORAD {norad_id}"
        )

        for error in validation["errors"]:

            print(f"        - {error}")

        return {
            "norad_id": norad_id,
            "status": "INVALID",
            "errors": validation["errors"]
        }


    print("[INFO] TLE validation successful")


    # --------------------------------------------------
    # STEP 3 — GET EPOCH
    # --------------------------------------------------

    epoch = validation["epoch"]

    print(
        f"[INFO] TLE epoch: {epoch.isoformat()}"
    )


    # --------------------------------------------------
    # STEP 4 — CHECK FRESHNESS
    # --------------------------------------------------

    fresh, freshness_error = check_tle_age(epoch)

    if not fresh:

        print(
            f"[WARNING] {freshness_error}"
        )

    else:

        print(
            "[INFO] TLE freshness check passed"
        )


    # --------------------------------------------------
    # STEP 5 — FIND EXISTING SATELLITE
    # --------------------------------------------------

    current_satellite = satellites_collection.find_one(
        {"norad_id": norad_id}
    )


    # --------------------------------------------------
    # STEP 6 — FIRST INSERTION
    # --------------------------------------------------

    if current_satellite is None:

        print(
            "[INFO] Satellite does not exist in database"
        )

        print(
            "[INFO] Performing first insertion"
        )


        now = datetime.now(timezone.utc)


        document = {

            "norad_id": norad_id,

            "name": tle["name"],

            "status": "ACTIVE",

            "tle": {

                "line1": tle["line1"],

                "line2": tle["line2"],

                "epoch": epoch,

                "source": "CelesTrak",

                "retrieved_at": now
            },

            "data_source": {

                "provider": "CelesTrak",

                "retrieved_at": now
            }
        }


        satellites_collection.insert_one(document)


        print(
            f"[SUCCESS] Inserted NORAD {norad_id}"
        )


        return {

            "norad_id": norad_id,

            "name": tle["name"],

            "status": "INSERTED"
        }


    # --------------------------------------------------
    # STEP 7 — EXISTING SATELLITE
    # --------------------------------------------------

    print(
        "[INFO] Satellite already exists in database"
    )


    current_tle = current_satellite.get("tle")


    if not current_tle:

        print(
            "[WARNING] Existing satellite has no TLE"
        )

        comparison = "NEW"

    else:

        current_epoch = current_tle.get("epoch")

        comparison = compare_tle_epochs(
            current_epoch,
            epoch
        )


    print(
        f"[INFO] TLE comparison result: {comparison}"
    )


    # --------------------------------------------------
    # STEP 8 — SAME TLE
    # --------------------------------------------------

    if comparison == "SAME":

        print(
            "[INFO] TLE epoch is unchanged"
        )

        print(
            "[INFO] No database update required"
        )

        return {

            "norad_id": norad_id,

            "name": tle["name"],

            "status": "UNCHANGED"
        }


    # --------------------------------------------------
    # STEP 9 — OLDER TLE
    # --------------------------------------------------

    if comparison == "OLDER":

        print(
            "[WARNING] New TLE is older than database TLE"
        )

        print(
            "[WARNING] Older TLE will not replace current TLE"
        )

        return {

            "norad_id": norad_id,

            "name": tle["name"],

            "status": "OLDER_TLE_IGNORED"
        }


    # --------------------------------------------------
    # STEP 10 — NEWER TLE
    # --------------------------------------------------

    if comparison == "NEW":

        print(
            "[INFO] Newer TLE detected"
        )


        # Save current TLE before replacement

        if current_tle:

            save_tle_history(
                history_collection,
                current_satellite
            )

            print(
                "[INFO] Previous TLE archived"
            )


        # Create updated TLE

        now = datetime.now(timezone.utc)


        updated_tle = {

            "line1": tle["line1"],

            "line2": tle["line2"],

            "epoch": epoch,

            "source": "CelesTrak",

            "retrieved_at": now
        }


        # Update satellite

        satellites_collection.update_one(

            {"norad_id": norad_id},

            {
                "$set": {

                    "name": tle["name"],

                    "tle": updated_tle,

                    "data_source": {

                        "provider": "CelesTrak",

                        "retrieved_at": now
                    }

                }
            }
        )


        print(
            f"[SUCCESS] Updated NORAD {norad_id}"
        )


        return {

            "norad_id": norad_id,

            "name": tle["name"],

            "status": "UPDATED"
        }

def save_ingestion_log(
    db,
    run_id,
    started_at,
    completed_at,
    results
):
    """
    Save one complete ingestion run to MongoDB.
    """

    duration_seconds = (
        completed_at - started_at
    ).total_seconds()

    inserted = 0
    updated = 0
    unchanged = 0
    older_ignored = 0
    failed = 0
    invalid = 0

    for result in results:

        status = result.get("status")

        if status == "INSERTED":
            inserted += 1

        elif status == "UPDATED":
            updated += 1

        elif status == "UNCHANGED":
            unchanged += 1

        elif status == "OLDER_TLE_IGNORED":
            older_ignored += 1

        elif status == "FAILED":
            failed += 1

        elif status == "INVALID":
            invalid += 1


    # An ingestion run is considered successful if
    # no satellite failed or had invalid data.

    if failed > 0 or invalid > 0:
        run_status = "PARTIAL_FAILURE"
    else:
        run_status = "SUCCESS"


    log_document = {

        "run_id": run_id,

        "started_at": started_at,

        "completed_at": completed_at,

        "duration_seconds": duration_seconds,

        "status": run_status,

        "source": "CelesTrak",

        "satellites_requested": len(SATELLITES),

        "satellites_processed": len(results),

        "inserted": inserted,

        "updated": updated,

        "unchanged": unchanged,

        "older_ignored": older_ignored,

        "failed": failed,

        "invalid": invalid,

        "satellite_results": results
    }


    db["ingestion_logs"].insert_one(
        log_document
    )


    print(
        "[INFO] Ingestion run logged to MongoDB"
    )

    print(
        f"[INFO] Run ID: {run_id}"
    )

def main():

    started_at = datetime.now(timezone.utc)

    run_id = (
        started_at.strftime("%Y%m%d-%H%M%S")
        + "-"
        + uuid.uuid4().hex[:8]
    )

    print(
        "[INFO] Connecting to MongoDB Atlas..."
    )

    print(
        f"[INFO] Ingestion run ID: {run_id}"
    )


    client = MongoClient(

        MONGODB_URI,

        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000
    )


    try:

        client.admin.command("ping")


        print(
            "[SUCCESS] MongoDB Atlas connection successful"
        )


        db = client[DB_NAME]


        satellites_collection = db["satellites"]

        history_collection = db["tle_history"]


        results = []


        for norad_id in SATELLITES:

            result = ingest_satellite(

                satellites_collection,

                history_collection,

                norad_id
            )


            results.append(result)


        # --------------------------------------------------
        # SUMMARY
        # --------------------------------------------------

        print()

        print("=" * 60)

        print("INGESTION SUMMARY")

        print("=" * 60)


        inserted = 0

        updated = 0

        unchanged = 0

        older = 0

        failed = 0

        invalid = 0


        for result in results:

            status = result["status"]


            if status == "INSERTED":

                inserted += 1


            elif status == "UPDATED":

                updated += 1


            elif status == "UNCHANGED":

                unchanged += 1


            elif status == "OLDER_TLE_IGNORED":

                older += 1


            elif status == "FAILED":

                failed += 1


            elif status == "INVALID":

                invalid += 1


        print(
            f"Total satellites : {len(results)}"
        )

        print(
            f"Inserted         : {inserted}"
        )

        print(
            f"Updated          : {updated}"
        )

        print(
            f"Unchanged        : {unchanged}"
        )

        print(
            f"Older ignored    : {older}"
        )

        print(
            f"Failed           : {failed}"
        )

        print(
            f"Invalid          : {invalid}"
        )

        print("=" * 60)

        completed_at = datetime.now(timezone.utc)

        save_ingestion_log(
            db,
            run_id,
            started_at,
            completed_at,
            results
        )

    finally:

        client.close()

        print(
            "[INFO] MongoDB connection closed"
        )


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)

    except Exception as error:
        print()
        print("=" * 60)
        print("INGESTION FAILED")
        print("=" * 60)
        print(error)
        print("=" * 60)

        sys.exit(1)