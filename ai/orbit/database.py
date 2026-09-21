"""MongoDB helpers for orbital state persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection

from .propagation import propagate_tle


def load_satellite_tle(
    satellites: Collection,
    satellite_id: int
) -> dict[str, Any]:
    """
    Load a satellite document and verify that it contains a complete TLE.

    The satellites collection is populated by Person 1's CelesTrak
    ingestion pipeline.
    """

    document = satellites.find_one({"norad_id": satellite_id})

    if document is None:
        raise LookupError(
            f"satellite {satellite_id} was not found"
        )

    tle = document.get("tle", {})

    if not tle.get("line1") or not tle.get("line2"):
        raise ValueError(
            f"satellite {satellite_id} has no complete TLE"
        )

    return document


def store_orbital_state(
    orbital_states: Collection,
    state: dict[str, Any]
) -> Any:
    """
    Store one propagated orbital state.

    The state is compatible with the ORBIT-X orbital_states
    time-series collection.
    """

    required = (
        "timestamp",
        "metadata",
        "position",
        "velocity",
    )

    missing = [
        field
        for field in required
        if field not in state
    ]

    if missing:
        raise ValueError(
            "orbital state is missing: "
            + ", ".join(missing)
        )

    return orbital_states.insert_one(state).inserted_id


def propagate_and_store(
    satellites: Collection,
    orbital_states: Collection,
    satellite_id: int,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """
    Load the current TLE for a satellite, propagate it using SGP4,
    and store the resulting orbital state.
    """

    timestamp = timestamp or datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        raise ValueError(
            "timestamp must include timezone information"
        )

    satellite = load_satellite_tle(
        satellites,
        satellite_id
    )

    tle = satellite["tle"]

    state = propagate_tle(
        satellite_id,
        tle["line1"],
        tle["line2"],
        timestamp,
    )

    store_orbital_state(
        orbital_states,
        state
    )

    return state


def propagate_all_and_store(
    satellites: Collection,
    orbital_states: Collection,
    timestamp: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Propagate every satellite that has a complete TLE.

    If one satellite fails, the remaining satellites are still
    processed.
    """

    timestamp = timestamp or datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        raise ValueError(
            "timestamp must include timezone information"
        )

    states: list[dict[str, Any]] = []

    for satellite in satellites.find(
        {},
        {
            "norad_id": 1,
            "tle": 1,
        }
    ):
        satellite_id = satellite.get("norad_id")
        tle = satellite.get("tle", {})

        if (
            satellite_id is None
            or not tle.get("line1")
            or not tle.get("line2")
        ):
            continue

        try:
            state = propagate_and_store(
                satellites,
                orbital_states,
                satellite_id,
                timestamp,
            )

            states.append(state)

        except Exception as error:
            print(
                f"[ERROR] Failed to propagate "
                f"NORAD {satellite_id}: {error}"
            )

            continue

    return states