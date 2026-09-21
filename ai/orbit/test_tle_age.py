from datetime import datetime, timedelta, timezone
import unittest

from .tle_validator import check_tle_age


class TLEAgeTests(unittest.TestCase):

    def test_future_epoch_is_rejected(self):
        future_epoch = (
            datetime.now(timezone.utc)
            + timedelta(days=3)
        )

        fresh, error = check_tle_age(
            future_epoch
        )

        self.assertFalse(fresh)
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()