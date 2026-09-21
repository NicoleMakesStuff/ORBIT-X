from datetime import datetime, timezone, timedelta
from sgp4.api import Satrec



def validate_sgp4_parse(line1, line2):
    """
    Check whether the TLE can be parsed by the SGP4 library.
    """

    try:

        satellite = Satrec.twoline2rv(
            line1,
            line2
        )

        if satellite.satnum <= 0:
            return False, "SGP4 returned an invalid satellite number"

        return True, None

    except Exception as error:

        return False, (
            f"SGP4 TLE parsing failed: {error}"
        )

def validate_norad_id(norad_id):
    """
    Validate a NORAD catalog number.
    """

    if norad_id is None:
        return False, "NORAD ID is missing"

    if not isinstance(norad_id, int):
        return False, "NORAD ID must be an integer"

    if norad_id <= 0:
        return False, "NORAD ID must be positive"

    return True, None


def validate_satellite_name(name):
    """
    Validate satellite name.
    """

    if not name:
        return False, "Satellite name is missing"

    if not name.strip():
        return False, "Satellite name is empty"

    return True, None


def validate_tle_lines(line1, line2):
    """
    Perform basic TLE structural validation.
    """

    errors = []

    # --------------------------------------------------
    # Line 1
    # --------------------------------------------------

    if not line1:
        errors.append("TLE Line 1 is missing")

    else:

        if not line1.startswith("1 "):
            errors.append(
                "TLE Line 1 must start with '1 '"
            )

        if len(line1) < 60:
            errors.append(
                "TLE Line 1 is too short"
            )

    # --------------------------------------------------
    # Line 2
    # --------------------------------------------------

    if not line2:
        errors.append("TLE Line 2 is missing")

    else:

        if not line2.startswith("2 "):
            errors.append(
                "TLE Line 2 must start with '2 '"
            )

        if len(line2) < 60:
            errors.append(
                "TLE Line 2 is too short"
            )

    if errors:
        return False, errors

    return True, []


def validate_tle_norad_match(norad_id, line1, line2):
    """
    Check whether the NORAD ID in the TLE
    matches the requested NORAD ID.
    """

    errors = []

    try:

        line1_norad = int(line1[2:7])

        line2_norad = int(line2[2:7])

    except (ValueError, IndexError):

        return False, [
            "Unable to extract NORAD ID from TLE"
        ]

    if line1_norad != norad_id:

        errors.append(
            f"Line 1 NORAD ID {line1_norad} "
            f"does not match requested {norad_id}"
        )

    if line2_norad != norad_id:

        errors.append(
            f"Line 2 NORAD ID {line2_norad} "
            f"does not match requested {norad_id}"
        )

    if errors:
        return False, errors

    return True, []


def parse_tle_epoch(line1):
    """
    Extract the TLE epoch from Line 1.

    TLE epoch format:
        YYDDD.DDDDDDDD

    where:
        YY  = two-digit year
        DDD = day of year
    """

    if len(line1) < 32:
        raise ValueError(
            "TLE Line 1 is too short to contain epoch"
        )

    epoch_text = line1[18:32].strip()

    if not epoch_text:
        raise ValueError(
            "TLE epoch is missing"
        )

    try:

        year = int(epoch_text[0:2])
        day_of_year = float(epoch_text[2:])

    except ValueError:

        raise ValueError(
            f"Invalid TLE epoch: {epoch_text}"
        )

    if day_of_year < 1.0 or day_of_year >= 367.0:
                raise ValueError(
                    f"Invalid TLE day-of-year: {day_of_year}"
                )

    # TLE convention:
    # 00-56 → 2000-2056
    # 57-99 → 1957-1999

    if year <= 56:
        full_year = 2000 + year
    else:
        full_year = 1900 + year

    day_integer = int(day_of_year)

    fractional_day = (
        day_of_year - day_integer
    )

    date = datetime(
        full_year,
        1,
        1,
        tzinfo=timezone.utc
    ) + timedelta(
        days=day_integer - 1,
        seconds=fractional_day * 86400
    )

    return date

def validate_tle_checksum(line):
    """
    Validate the checksum digit of a TLE line.
    """

    if not line:
        return False, "TLE line is missing"

    if len(line) < 2:
        return False, "TLE line is too short"

    checksum_character = line[-1]

    if not checksum_character.isdigit():
        return False, "TLE checksum character is not a digit"

    expected_checksum = int(checksum_character)

    total = 0

    for character in line[:-1]:

        if character.isdigit():
            total += int(character)

        elif character == "-":
            total += 1

    calculated_checksum = total % 10

    if calculated_checksum != expected_checksum:

        return False, (
            f"Invalid checksum: expected {expected_checksum}, "
            f"calculated {calculated_checksum}"
        )

    return True, None

def validate_tle_checksums(line1, line2):
    """
    Validate checksums for both TLE lines.
    """

    errors = []

    valid, error = validate_tle_checksum(line1)

    if not valid:
        errors.append(f"Line 1: {error}")

    valid, error = validate_tle_checksum(line2)

    if not valid:
        errors.append(f"Line 2: {error}")

    if errors:
        return False, errors

    return True, []

def validate_complete_tle(
    norad_id,
    name,
    line1,
    line2
):
    """
    Run all validation checks.
    """

    errors = []

    # NORAD ID

    valid, error = validate_norad_id(
        norad_id
    )

    if not valid:
        errors.append(error)

    # Satellite name

    valid, error = validate_satellite_name(
        name
    )

    if not valid:
        errors.append(error)

    # TLE structure

    valid, tle_errors = validate_tle_lines(
        line1,
        line2
    )

    if not valid:
        errors.extend(tle_errors)

    if not errors:

        valid, checksum_errors = validate_tle_checksums(
            line1,
            line2
        )

        if not valid:
            errors.extend(checksum_errors)

    # NORAD consistency

    if not errors:

        valid, tle_errors = validate_tle_norad_match(
            norad_id,
            line1,
            line2
        )

        if not valid:
            errors.extend(tle_errors)

    if not errors:

        valid, sgp4_error = validate_sgp4_parse(
            line1,
            line2
        )

        if not valid:
            errors.append(sgp4_error)

    # Epoch

    epoch = None

    if not errors:

        try:

            epoch = parse_tle_epoch(
                line1
            )

        except ValueError as error:

            errors.append(str(error))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "epoch": epoch
    }
def check_tle_age(epoch, max_age_days=7):
    """
    Check whether a TLE is reasonably recent.

    A TLE is considered invalid if:
    - it is missing
    - its epoch is in the future
    - it is older than max_age_days
    """

    if epoch is None:
        return False, "TLE epoch is missing"

    now = datetime.now(timezone.utc)

    age = now - epoch

    age_days = age.total_seconds() / 86400

    if age_days < 0:
        return False, (
            f"TLE epoch is {abs(age_days):.1f} days in the future"
        )

    if age_days > max_age_days:
        return False, (
            f"TLE is {age_days:.1f} days old"
        )

    return True, None