import os
import unittest

from dotenv import load_dotenv
from pymongo import MongoClient

from .tle_validator import (
    validate_complete_tle,
    check_tle_age
)


class TLEValidatorTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Load MongoDB configuration from backend/.env
        and connect to the orbit_x database.
        """

        # ORBIT-X/
        project_root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                ".."
            )
        )

        # ORBIT-X/backend/.env
        env_path = os.path.join(
            project_root,
            "backend",
            ".env"
        )

        print(f"\nLoading environment from: {env_path}")

        # Explicitly load the .env file.
        load_dotenv(
            dotenv_path=env_path,
            override=True
        )

        mongo_uri = os.getenv("MONGODB_URI")

        if not mongo_uri:
            raise RuntimeError(
                f"MONGO_URI not found in {env_path}"
            )

        cls.client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000
        )

        # Verify connection immediately.
        cls.client.admin.command("ping")

        db_name = os.getenv("MONGODB_DB_NAME")

        if not db_name:
            raise RuntimeError(
                f"MONGODB_DB_NAME not found in {env_path}"
            )

        cls.db = cls.client[db_name]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "client") and cls.client:
            cls.client.close()

    def test_valid_tle(self):
        """
        Validate a real TLE currently stored in MongoDB.
        """

        satellite = self.db.satellites.find_one(
            {
                "norad_id": 25544
            }
        )

        self.assertIsNotNone(
            satellite,
            "NORAD 25544 was not found in satellites collection"
        )

        tle = satellite.get("tle")

        self.assertIsNotNone(
            tle,
            "Satellite does not contain a TLE"
        )

        result = validate_complete_tle(
            satellite["norad_id"],
            satellite["name"],
            tle["line1"],
            tle["line2"]
        )

        self.assertTrue(
            result["valid"],
            f"TLE should be valid, errors: {result['errors']}"
        )

        self.assertIsNotNone(
            result["epoch"]
        )

    def test_invalid_tle_is_rejected(self):
        """
        Corrupt the checksum of Line 1 and verify
        that the validator rejects the TLE.
        """

        satellite = self.db.satellites.find_one(
            {
                "norad_id": 25544
            }
        )

        self.assertIsNotNone(
            satellite,
            "NORAD 25544 was not found in satellites collection"
        )

        tle = satellite["tle"]

        line1 = tle["line1"]
        line2 = tle["line2"]

        # Change the final checksum digit.
        original_checksum = line1[-1]

        replacement = (
            "0"
            if original_checksum != "0"
            else "1"
        )

        invalid_line1 = (
            line1[:-1] +
            replacement
        )

        result = validate_complete_tle(
            satellite["norad_id"],
            satellite["name"],
            invalid_line1,
            line2
        )

        self.assertFalse(
            result["valid"]
        )

        self.assertTrue(
            any(
                "checksum" in error.lower()
                for error in result["errors"]
            ),
            f"Expected checksum error, got: {result['errors']}"
        )

    def test_epoch_freshness_function_exists(self):
        """
        Verify that the TLE age checker rejects
        a future TLE epoch.
        """

        from datetime import datetime, timedelta, timezone

        future_epoch = (
            datetime.now(timezone.utc)
            + timedelta(days=3)
        )

        valid, error = check_tle_age(
            future_epoch
        )

        self.assertFalse(valid)
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()