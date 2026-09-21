from datetime import datetime, timezone
import unittest

from .tle_updater import compare_tle_epochs


class TLEUpdaterTests(unittest.TestCase):

    def setUp(self):
        self.current = datetime(
            2026, 9, 18,
            tzinfo=timezone.utc
        )

        self.newer = datetime(
            2026, 9, 19,
            tzinfo=timezone.utc
        )

        self.older = datetime(
            2026, 9, 17,
            tzinfo=timezone.utc
        )

        self.same = datetime(
            2026, 9, 18,
            tzinfo=timezone.utc
        )

    def test_newer_tle(self):
        result = compare_tle_epochs(
            self.current,
            self.newer
        )

        self.assertEqual(result, "NEW")

    def test_older_tle(self):
        result = compare_tle_epochs(
            self.current,
            self.older
        )

        self.assertEqual(result, "OLDER")

    def test_same_tle(self):
        result = compare_tle_epochs(
            self.current,
            self.same
        )

        self.assertEqual(result, "SAME")


if __name__ == "__main__":
    unittest.main()