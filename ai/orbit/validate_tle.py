def validate_tle(norad_id, name, line1, line2):
    errors = []

    # NORAD ID
    if not norad_id:
        errors.append("Missing NORAD ID")

    # Satellite name
    if not name or not name.strip():
        errors.append("Missing satellite name")

    # TLE Line 1
    if not line1:
        errors.append("Missing TLE line 1")
    elif not line1.startswith("1 "):
        errors.append("Invalid TLE line 1")

    # TLE Line 2
    if not line2:
        errors.append("Missing TLE line 2")
    elif not line2.startswith("2 "):
        errors.append("Invalid TLE line 2")

    # Basic TLE length check
    if line1 and len(line1) < 60:
        errors.append("TLE line 1 appears too short")

    if line2 and len(line2) < 60:
        errors.append("TLE line 2 appears too short")

    return errors