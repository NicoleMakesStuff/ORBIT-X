from datetime import datetime, timezone

from sgp4.api import Satrec
from sgp4.api import jday


def propagate_tle(line1, line2):

    satellite = Satrec.twoline2rv(
        line1,
        line2
    )

    now = datetime.now(timezone.utc)

    jd, fr = jday(
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        now.second
        + now.microsecond / 1_000_000
    )

    error_code, position, velocity = satellite.sgp4(
        jd,
        fr
    )

    if error_code != 0:
        raise RuntimeError(
            f"SGP4 propagation failed: "
            f"error code {error_code}"
        )

    return {
        "position_km": {
            "x": position[0],
            "y": position[1],
            "z": position[2]
        },

        "velocity_km_s": {
            "x": velocity[0],
            "y": velocity[1],
            "z": velocity[2]
        },

        "timestamp": now
    }