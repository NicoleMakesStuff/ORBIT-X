import unittest
from datetime import datetime, timezone

from orbit.propagation import propagate_tle


class PropagationTests(unittest.TestCase):
    def test_iss_propagates_to_reasonable_geodetic_coordinates(self):
        state = propagate_tle(
            25544,
            "1 25544U 98067A   24140.51840337  .00016717  00000-0  30212-3 0  9995",
            "2 25544  51.6401  52.9545 0004758  75.9638  44.1552 15.50012345453123",
            datetime(2024, 5, 19, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(state["metadata"]["satellite_id"], 25544)
        self.assertEqual(state["propagation_method"], "SGP4")
        self.assertGreaterEqual(state["position"]["latitude"], -90)
        self.assertLessEqual(state["position"]["latitude"], 90)
        self.assertGreaterEqual(state["position"]["longitude"], -180)
        self.assertLessEqual(state["position"]["longitude"], 180)
        self.assertGreater(state["position"]["altitude_km"], 300)
        self.assertLess(state["position"]["altitude_km"], 500)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            propagate_tle(
                25544,
                "1 25544U 98067A   24140.51840337  .00016717  00000-0  30212-3 0  9995",
                "2 25544  51.6401  52.9545 0004758  75.9638  44.1552 15.50012345453123",
                datetime(2024, 5, 19, 12, 0),
            )


if __name__ == "__main__":
    unittest.main()