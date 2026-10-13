"""Ground-station look angles and satellite pass prediction."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from .propagation import _teme_to_ecef, _julian_date, propagate_tle


EARTH_EQUATORIAL_RADIUS_KM = 6378.137
EARTH_ECCENTRICITY_SQUARED = 0.0066943799901413165


def _geodetic_to_ecef(latitude: float, longitude: float, altitude_km: float) -> tuple[float, float, float]:
    latitude_radians = math.radians(latitude)
    longitude_radians = math.radians(longitude)
    sine = math.sin(latitude_radians)
    normal = EARTH_EQUATORIAL_RADIUS_KM / math.sqrt(
        1 - EARTH_ECCENTRICITY_SQUARED * sine**2
    )
    return (
        (normal + altitude_km) * math.cos(latitude_radians) * math.cos(longitude_radians),
        (normal + altitude_km) * math.cos(latitude_radians) * math.sin(longitude_radians),
        (normal * (1 - EARTH_ECCENTRICITY_SQUARED) + altitude_km) * sine,
    )


def look_angles(state: dict[str, Any], station: dict[str, Any]) -> dict[str, float | bool]:
    coordinates = station["location"]["coordinates"]
    longitude, latitude = coordinates[0], coordinates[1]
    altitude_km = station.get("altitude_km", 0.0)
    station_ecef = _geodetic_to_ecef(latitude, longitude, altitude_km)

    timestamp = state["timestamp"]
    position = state["_teme_position_km"]
    satellite_ecef = _teme_to_ecef(position, timestamp)
    delta = tuple(satellite_ecef[index] - station_ecef[index] for index in range(3))

    latitude_radians = math.radians(latitude)
    longitude_radians = math.radians(longitude)
    east = -math.sin(longitude_radians) * delta[0] + math.cos(longitude_radians) * delta[1]
    north = (
        -math.sin(latitude_radians) * math.cos(longitude_radians) * delta[0]
        - math.sin(latitude_radians) * math.sin(longitude_radians) * delta[1]
        + math.cos(latitude_radians) * delta[2]
    )
    up = (
        math.cos(latitude_radians) * math.cos(longitude_radians) * delta[0]
        + math.cos(latitude_radians) * math.sin(longitude_radians) * delta[1]
        + math.sin(latitude_radians) * delta[2]
    )
    horizontal_range = math.hypot(east, north)
    return {
        "azimuth_deg": math.degrees(math.atan2(east, north)) % 360.0,
        "elevation_deg": math.degrees(math.atan2(up, horizontal_range)),
        "range_km": math.sqrt(east**2 + north**2 + up**2),
        "visible": up > 0,
    }


def _state_with_raw_position(state: dict[str, Any], position: tuple[float, float, float]) -> dict[str, Any]:
    enriched = dict(state)
    enriched["_teme_position_km"] = position
    return enriched


def look_angles_at(
    satellite_id: int,
    line1: str,
    line2: str,
    station: dict[str, Any],
    timestamp: datetime,
) -> dict[str, float | bool]:
    state = propagate_tle(satellite_id, line1, line2, timestamp)
    day, fraction = _julian_date(timestamp)
    from sgp4.api import Satrec

    satellite = Satrec.twoline2rv(line1, line2)
    error, position, _ = satellite.sgp4(day, fraction)
    if error != 0:
        raise ValueError(f"SGP4 propagation failed with error code {error}")
    return look_angles(_state_with_raw_position(state, tuple(position)), station)


def predict_next_pass(
    satellite_id: int,
    line1: str,
    line2: str,
    station: dict[str, Any],
    start: datetime,
    search_minutes: int = 180,
    step_seconds: int = 30,
    elevation_mask_deg: float = 0.0,
) -> dict[str, Any] | None:
    if start.tzinfo is None:
        raise ValueError("start must include timezone information")

    current = start.astimezone(timezone.utc)
    previous = look_angles_at(satellite_id, line1, line2, station, current)
    aos = None
    tca = None
    maximum_elevation = float("-inf")
    samples = search_minutes * 60 // step_seconds
    for _ in range(samples + 1):
        current += timedelta(seconds=step_seconds)
        angles = look_angles_at(satellite_id, line1, line2, station, current)
        above = angles["elevation_deg"] >= elevation_mask_deg
        was_above = previous["elevation_deg"] >= elevation_mask_deg
        if aos is None and above and not was_above:
            aos = current
        if aos is not None and above and angles["elevation_deg"] > maximum_elevation:
            maximum_elevation = angles["elevation_deg"]
            tca = current
        if aos is not None and not above and was_above:
            return {
                "aos": aos,
                "los": current,
                "tca": tca,
                "maximum_elevation_deg": maximum_elevation,
            }
        previous = angles

    return None


def store_pass_event(communication_events: Any, satellite_id: int, station_id: str, pass_result: dict[str, Any]) -> Any:
    """Persist a predicted visibility window in communication_events."""
    if not pass_result or not pass_result.get("aos") or not pass_result.get("los"):
        raise ValueError("a complete pass result is required")
    document = {
        "satellite_id": satellite_id,
        "ground_station_id": station_id,
        "start_time": pass_result["aos"],
        "end_time": pass_result["los"],
        "status": "SUCCESS",
    }
    return communication_events.insert_one(document).inserted_id