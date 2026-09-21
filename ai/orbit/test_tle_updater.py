from datetime import datetime, timezone

from tle_updater import compare_tle_epochs


current = datetime(
    2026,
    9,
    18,
    tzinfo=timezone.utc
)

newer = datetime(
    2026,
    9,
    19,
    tzinfo=timezone.utc
)

older = datetime(
    2026,
    9,
    17,
    tzinfo=timezone.utc
)

same = datetime(
    2026,
    9,
    18,
    tzinfo=timezone.utc
)


print("NEW test:")

print(
    compare_tle_epochs(
        current,
        newer
    )
)


print("OLDER test:")

print(
    compare_tle_epochs(
        current,
        older
    )
)


print("SAME test:")

print(
    compare_tle_epochs(
        current,
        same
    )
)