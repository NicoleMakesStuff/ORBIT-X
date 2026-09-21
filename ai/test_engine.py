import unittest
from datetime import datetime, timezone

from orbit.engine import run_once


LINE1 = "1 25544U 98067A   24140.51840337  .00016717  00000-0  30212-3 0  9995"
LINE2 = "2 25544  51.6401  52.9545 0004758  75.9638  44.1552 15.50012345453123"
TIMESTAMP = datetime(2024, 5, 19, 12, 0, tzinfo=timezone.utc)


class Collection:
    def __init__(self, documents=None):
        self.documents = documents or []
        self.inserted = []

    def find(self, query, projection=None):
        return self.documents

    def find_one(self, query):
        for document in self.documents:
            if document.get("norad_id") == query.get("norad_id"):
                return document
        return None

    def insert_one(self, document):
        self.inserted.append(document)
        return type("Result", (), {"inserted_id": "id"})()

    def insert_many(self, documents):
        self.inserted.extend(documents)
        return type("Result", (), {"inserted_ids": ["id"] * len(documents)})()


class Database(dict):
    def __getitem__(self, name):
        return super().__getitem__(name)


class EngineTests(unittest.TestCase):
    def test_run_once_persists_orbit_and_telemetry(self):
        database = Database({
            "satellites": Collection([{"norad_id": 25544, "tle": {"line1": LINE1, "line2": LINE2}}]),
            "orbital_states": Collection(),
            "telemetry": Collection(),
            "alerts": Collection(),
        })

        counts = run_once(database, timestamp=TIMESTAMP, telemetry_seed=4)

        self.assertEqual(counts["orbital_states"], 1)
        self.assertEqual(counts["telemetry"], 1)
        self.assertEqual(len(database["orbital_states"].inserted), 1)
        self.assertEqual(len(database["telemetry"].inserted), 1)


if __name__ == "__main__":
    unittest.main()