import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

from celestrak import get_tle


load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

DB_NAME = os.getenv(
    "MONGODB_DB_NAME",
    "orbit_x"
)

SATELLITES = [
    25544
]


def main():

    client = MongoClient(MONGODB_URI)

    db = client[DB_NAME]

    satellites = db["satellites"]

    for norad_id in SATELLITES:

        print(
            f"Fetching NORAD {norad_id}..."
        )

        try:

            tle = get_tle(norad_id)

            document = {
                "norad_id": norad_id,

                "name": tle["name"],

                "status": "ACTIVE",

                "tle": {
                    "line1": tle["line1"],
                    "line2": tle["line2"],
                    "source": "CelesTrak",
                    "retrieved_at": datetime.now(
                        timezone.utc
                    )
                },

                "data_source": {
                    "provider": "CelesTrak",
                    "retrieved_at": datetime.now(
                        timezone.utc
                    )
                }
            }

            satellites.update_one(
                {"norad_id": norad_id},
                {"$set": document},
                upsert=True
            )

            print(
                f"Stored {tle['name']}"
            )

        except Exception as error:

            print(
                f"Failed for {norad_id}: "
                f"{error}"
            )

    client.close()


if __name__ == "__main__":
    main()