"""MongoDB helpers for orbital state persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection

from .propagation import propagate_tle


def load_satellite_tle(satellites: Collection, satellite_id: int) -> dict[str, Any]:
    document = satellites.find_one({"norad_id": satellite_id})
    if document is None:
        raise LookupError(f"satellite {satellite_id} was not found")

    tle = document.get("tle", {})
    if not tle.get("line1") or not tle.get("line2"):
        raise ValueError(f"satellite {satellite_id} has no complete TLE")
    return document


def store_orbital_state(orbital_states: Collection, state: dict[str, Any]) -> Any:
    required = ("timestamp", "metadata", "position", "velocity")
    missing = [field for field in required if field not in state]
    if missing:
        raise ValueError(f"orbital state is missing: {', '.join(missing)}")

    return orbital_states.insert_one(state).inserted_id


def propagate_and_store(
    satellites: Collection,
    orbital_states: Collection,
    satellite_id: int,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    timestamp = timestamp or datetime.now(timezone.utc)
    satellite = load_satellite_tle(satellites, satellite_id)
    state = propagate_tle(
        satellite_id,
        satellite["tle"]["line1"],
        satellite["tle"]["line2"],
        timestamp,
    )
    store_orbital_state(orbital_states, state)
    return state


def propagate_all_and_store(
    satellites: Collection,
    orbital_states: Collection,
    timestamp: datetime | None = None,
) -> list[dict[str, Any]]:
    """Propagate every satellite with a complete TLE for scheduled jobs."""
    states = []
    for satellite in satellites.find({}, {"norad_id": 1, "tle": 1}):
        satellite_id = satellite.get("norad_id")
        tle = satellite.get("tle", {})
        if satellite_id is None or not tle.get("line1") or not tle.get("line2"):
            continue
        states.append(
            propagate_and_store(satellites, orbital_states, satellite_id, timestamp)
        )
    return states