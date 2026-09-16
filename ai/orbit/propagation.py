"""SGP4 propagation and TEME-to-geodetic coordinate conversion."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from sgp4.api import Satrec
from sgp4.conveniences import sat_epoch_datetime


EARTH_RADIUS_KM = 6378.137
EARTH_FLATTENING = 1 / 298.257223563


def _julian_date(timestamp: datetime) -> tuple[float, float]:
    """Return a UTC datetime as the two-part Julian date used by SGP4."""
    timestamp = timestamp.astimezone(timezone.utc)
    seconds = timestamp.timestamp()
    julian_date = seconds / 86400.0 + 2440587.5
    whole_day = math.floor(julian_date)
    return whole_day, julian_date - whole_day


def _gmst_radians(julian_date: float) -> float:
    centuries = (julian_date - 2451545.0) / 36525.0
    angle_degrees = (
        280.46061837
        + 360.98564736629 * (julian_date - 2451545.0)
        + 0.000387933 * centuries**2
        - centuries**3 / 38710000.0
    )
    return math.radians(angle_degrees % 360.0)


def _teme_to_ecef(position_km: tuple[float, float, float], timestamp: datetime) -> tuple[float, float, float]:
    julian_date = timestamp.timestamp() / 86400.0 + 2440587.5
    theta = _gmst_radians(julian_date)
    cosine = math.cos(theta)
    sine = math.sin(theta)
    x, y, z = position_km
    return cosine * x + sine * y, -sine * x + cosine * y, z


def _ecef_to_geodetic(ecef_km: tuple[float, float, float]) -> dict[str, float]:
    x, y, z = ecef_km
    semi_minor = EARTH_RADIUS_KM * (1 - EARTH_FLATTENING)
    eccentricity_squared = 1 - (semi_minor / EARTH_RADIUS_KM) ** 2
    longitude = math.atan2(y, x)
    distance_from_axis = math.hypot(x, y)
    latitude = math.atan2(z, distance_from_axis * (1 - eccentricity_squared))

    for _ in range(10):
        sine = math.sin(latitude)
        radius = EARTH_RADIUS_KM / math.sqrt(1 - eccentricity_squared * sine**2)
        latitude = math.atan2(z + eccentricity_squared * radius * sine, distance_from_axis)

    sine = math.sin(latitude)
    radius = EARTH_RADIUS_KM / math.sqrt(1 - eccentricity_squared * sine**2)
    altitude = distance_from_axis / math.cos(latitude) - radius

    return {
        "latitude": math.degrees(latitude),
        "longitude": math.degrees(longitude),
        "altitude_km": altitude,
    }


def propagate_tle(
    satellite_id: int,
    line1: str,
    line2: str,
    timestamp: datetime,
) -> dict[str, Any]:
    """Propagate a TLE and return a document compatible with orbital_states."""
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must include timezone information")

    try:
        satellite = Satrec.twoline2rv(line1, line2)
    except Exception as error:
        raise ValueError("invalid TLE lines") from error

    julian_day, julian_fraction = _julian_date(timestamp)
    error_code, position, velocity = satellite.sgp4(julian_day, julian_fraction)
    if error_code != 0:
        raise ValueError(f"SGP4 propagation failed with error code {error_code}")

    ecef = _teme_to_ecef(tuple(position), timestamp)
    geodetic = _ecef_to_geodetic(ecef)
    propagated_at = timestamp.astimezone(timezone.utc)

    return {
        "timestamp": propagated_at,
        "metadata": {"satellite_id": satellite_id},
        "position": geodetic,
        "velocity": {
            "x_km_s": velocity[0],
            "y_km_s": velocity[1],
            "z_km_s": velocity[2],
        },
        "propagation_method": "SGP4",
        "tle_epoch": sat_epoch_datetime(satellite).astimezone(timezone.utc),
    }