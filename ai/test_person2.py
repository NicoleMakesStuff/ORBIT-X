import unittest
from datetime import datetime, timezone

from orbit.database import propagate_all_and_store, propagate_and_store
from orbit.propagation import propagate_tle
from orbit.telemetry import detect_anomalies, simulate_telemetry
from orbit.visibility import look_angles_at


LINE1 = "1 25544U 98067A   24140.51840337  .00016717  00000-0  30212-3 0  9995"
LINE2 = "2 25544  51.6401  52.9545 0004758  75.9638  44.1552 15.50012345453123"
TIMESTAMP = datetime(2024, 5, 19, 12, 0, tzinfo=timezone.utc)
STATION = {
    "station_id": "GS-001",
    "location": {"type": "Point", "coordinates": [79.1637, 12.9692]},
}


class FakeInsertResult:
    inserted_id = "state-1"


class FakeCollection:
    def __init__(self, document=None):
        self.document = document
        self.inserted = []

    def find_one(self, query):
        if self.document and self.document.get("norad_id") == query["norad_id"]:
            return self.document
        return None

    def find(self, query, projection):
        return [self.document] if self.document else []

    def insert_one(self, document):
        self.inserted.append(document)
        return FakeInsertResult()


class Person2Tests(unittest.TestCase):
    def test_look_angles_have_valid_ranges(self):
        angles = look_angles_at(25544, LINE1, LINE2, STATION, TIMESTAMP)
        self.assertGreaterEqual(angles["azimuth_deg"], 0)
        self.assertLess(angles["azimuth_deg"], 360)
        self.assertGreaterEqual(angles["elevation_deg"], -90)
        self.assertLessEqual(angles["elevation_deg"], 90)
        self.assertGreater(angles["range_km"], 0)

    def test_propagate_and_store_loads_tle_and_inserts_state(self):
        satellites = FakeCollection({"norad_id": 25544, "tle": {"line1": LINE1, "line2": LINE2}})
        orbital_states = FakeCollection()
        state = propagate_and_store(satellites, orbital_states, 25544, TIMESTAMP)
        self.assertEqual(state["metadata"]["satellite_id"], 25544)
        self.assertEqual(len(orbital_states.inserted), 1)

    def test_batch_propagation_inserts_each_complete_tle(self):
        satellites = FakeCollection({"norad_id": 25544, "tle": {"line1": LINE1, "line2": LINE2}})
        orbital_states = FakeCollection()
        states = propagate_all_and_store(satellites, orbital_states, TIMESTAMP)
        self.assertEqual(len(states), 1)

    def test_seeded_telemetry_is_repeatable_and_alerts_are_generated(self):
        first = simulate_telemetry(25544, TIMESTAMP, seed=7)
        second = simulate_telemetry(25544, TIMESTAMP, seed=7)
        self.assertEqual(first, second)
        first["power"]["battery_percent"] = 10
        alerts = detect_anomalies(first)
        self.assertEqual(alerts[0]["parameter"], "power.battery_percent")

    def test_invalid_tle_is_rejected(self):
        with self.assertRaises(ValueError):
            propagate_tle(25544, "bad", "bad", TIMESTAMP)

    def test_next_pass_contains_aos_tca_los_and_peak_elevation(self):
        from orbit.visibility import predict_next_pass, store_pass_event

        result = predict_next_pass(
            25544,
            LINE1,
            LINE2,
            STATION,
            TIMESTAMP,
            search_minutes=1440,
        )
        self.assertIsNotNone(result)
        self.assertLess(result["aos"], result["tca"])
        self.assertLess(result["tca"], result["los"])
        self.assertGreater(result["maximum_elevation_deg"], 0)

        events = FakeCollection()
        event_id = store_pass_event(events, 25544, "GS-001", result)
        self.assertEqual(event_id, "state-1")
        self.assertEqual(events.inserted[0]["ground_station_id"], "GS-001")


if __name__ == "__main__":
    unittest.main()