from celestrak import get_tle

from tle_validator import (
    validate_complete_tle,
    check_tle_age
)


NORAD_ID = 25544


print("=" * 60)
print("ORBIT-X TLE VALIDATION TEST")
print("=" * 60)


print("[INFO] Fetching real TLE from CelesTrak...")


tle = get_tle(NORAD_ID)
tle["line1"] = tle["line1"][:-1] + "0"

print()
print("Satellite:")
print(tle["name"])

print()
print("Line 1:")
print(tle["line1"])

print()
print("Line 2:")
print(tle["line2"])


print()
print("[INFO] Running validation...")


validation = validate_complete_tle(
    NORAD_ID,
    tle["name"],
    tle["line1"],
    tle["line2"]
)


print()
print("=" * 60)


if validation["valid"]:

    print("VALIDATION RESULT: PASS")

    print(
        f"Epoch: {validation['epoch'].isoformat()}"
    )

else:

    print("VALIDATION RESULT: FAIL")

    print("Errors:")

    for error in validation["errors"]:

        print(f" - {error}")


print("=" * 60)


if validation["epoch"]:

    fresh, error = check_tle_age(
        validation["epoch"]
    )

    print()

    if fresh:
        print("FRESHNESS RESULT: PASS")
    else:
        print("FRESHNESS RESULT: FAIL")
        print(error)