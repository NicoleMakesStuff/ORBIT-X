import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

from propagator import propagate_tle


# --------------------------------------------------
# Load ORBIT-X environment
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "backend" / ".env"

load_dotenv(ENV_FILE)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "orbit_x")


# --------------------------------------------------
# Connect to MongoDB Atlas
# --------------------------------------------------

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

satellite = db["satellites"].find_one({
    "norad_id": 25544
})


# --------------------------------------------------
# Make sure satellite exists
# --------------------------------------------------

if satellite is None:
    raise RuntimeError(
        "NORAD 25544 was not found in the satellites collection."
    )


# --------------------------------------------------
# Get TLE
# --------------------------------------------------

line1 = satellite["tle"]["line1"]
line2 = satellite["tle"]["line2"]

print("Satellite:", satellite["name"])
print("NORAD ID:", satellite["norad_id"])
print()
print("TLE Line 1:")
print(line1)
print()
print("TLE Line 2:")
print(line2)
print()


# --------------------------------------------------
# Propagate
# --------------------------------------------------

result = propagate_tle(
    line1,
    line2
)


# --------------------------------------------------
# Display result
# --------------------------------------------------

print("SGP4 propagation successful!")
print()
print("Position (km):")
print(result["position_km"])

print()
print("Velocity (km/s):")
print(result["velocity_km_s"])

print()
print("Timestamp:")
print(result["timestamp"])


client.close()