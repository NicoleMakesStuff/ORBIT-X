import os
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

from propagator import propagate_tle
from coordinates import teme_to_ecef, ecef_to_geodetic


# --------------------------------------------------
# Load ORBIT-X environment
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / "backend" / ".env"

load_dotenv(ENV_FILE)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "orbit_x")

print("Environment file:", ENV_FILE)
print("Database:", DB_NAME)

if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI was not found in backend/.env"
    )



import math

from sgp4.api import Satrec, jday



load_dotenv()




def propagate(
    line1,
    line2,
    timestamp
):

    satellite = Satrec.twoline2rv(
        line1,
        line2
    )

    jd, fr = jday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour,
        timestamp.minute,
        timestamp.second
        + timestamp.microsecond / 1_000_000
    )

    error_code, position, velocity = (
        satellite.sgp4(jd, fr)
    )

    if error_code != 0:

        raise RuntimeError(
            f"SGP4 failed: {error_code}"
        )

    x, y, z = position

    vx, vy, vz = velocity

    ecef = teme_to_ecef(
        x,
        y,
        z,
        jd + fr
    )

    latitude, longitude, altitude = (
        ecef_to_geodetic(
            *ecef
        )
    )

    velocity_magnitude = math.sqrt(
        vx * vx
        + vy * vy
        + vz * vz
    )

    return {
        "position": {
            "latitude": latitude,
            "longitude": longitude,
            "altitude_km": altitude
        },

        "velocity_km_s": velocity_magnitude,

        "timestamp": timestamp
    }


def main():

    client = MongoClient(
        MONGODB_URI
    )

    db = client[DB_NAME]

    satellites = db["satellites"]

    orbital_states = db[
        "orbital_states"
    ]

    timestamp = datetime.now(
        timezone.utc
    )

    for satellite in satellites.find(
        {
            "tle.line1": {
                "$exists": True
            },

            "tle.line2": {
                "$exists": True
            }
        }
    ):

        try:

            result = propagate(
                satellite["tle"]["line1"],
                satellite["tle"]["line2"],
                timestamp
            )

            document = {
                "timestamp": timestamp,

                "metadata": {
                    "satellite_id":
                        satellite["norad_id"]
                },

                "position":
                    result["position"],

                "velocity_km_s":
                    result["velocity_km_s"],

                "eclipse": False
            }

            orbital_states.insert_one(
                document
            )

            print(
                f'{satellite["name"]}: '
                f'{result["position"]}'
            )

        except Exception as error:

            print(
                f'Failed for '
                f'{satellite["norad_id"]}: '
                f'{error}'
            )

    client.close()


if __name__ == "__main__":
    main()