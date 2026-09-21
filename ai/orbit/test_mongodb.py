import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
import certifi


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / "backend" / ".env"

load_dotenv(ENV_FILE)

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI not found")


print("Testing MongoDB connection...")
print(f"Environment file: {ENV_FILE}")

client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)

try:

    result = client.admin.command("ping")

    print("MongoDB ping successful!")
    print(result)

finally:

    client.close()

    print("MongoDB connection closed")