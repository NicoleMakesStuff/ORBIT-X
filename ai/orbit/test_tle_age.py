from datetime import datetime, timedelta, timezone

from tle_validator import check_tle_age


future_epoch = (
    datetime.now(timezone.utc)
    + timedelta(days=3)
)


fresh, error = check_tle_age(
    future_epoch
)


print("Fresh:", fresh)
print("Message:", error)