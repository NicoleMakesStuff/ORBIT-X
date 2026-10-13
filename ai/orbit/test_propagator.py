import unittest
from datetime import datetime, timezone

from .propagation import propagate_tle


class PropagationIntegrationTests(unittest.TestCase):

    NORAD_ID = 25544

    LINE1 = (
        "1 25544U 98067A   26261.14280072  "
        ".00012585  00000-0  23156-3 0  9990"
    )

    LINE2 = (
        "2 25544  51.6351  78.3284 0002366 "
        "103.3218 256.8207 15.49232739533616"
    )

    def test_iss_propagation(self):

        timestamp = datetime.now(
            timezone.utc
        )

        result = propagate_tle(
            self.NORAD_ID,
            self.LINE1,
            self.LINE2,
            timestamp,
        )

        self.assertIn(
            "position",
            result
        )

        self.assertIn(
            "velocity",
            result
        )

        self.assertIn(
            "orbital",
            result
        )

        self.assertIn(
            "tle_epoch",
            result
        )

        position = result["position"]

        self.assertIn(
            "latitude",
            position
        )

        self.assertIn(
            "longitude",
            position
        )

        self.assertIn(
            "altitude_km",
            position
        )

        self.assertGreater(
            position["altitude_km"],
            300
        )

        self.assertLess(
            position["altitude_km"],
            500
        )

    def test_timezone_is_required(self):

        timestamp = datetime.now()

        with self.assertRaises(ValueError):
            propagate_tle(
                self.NORAD_ID,
                self.LINE1,
                self.LINE2,
                timestamp,
            )


if __name__ == "__main__":
    unittest.main()