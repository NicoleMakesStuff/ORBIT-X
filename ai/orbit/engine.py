"""Mongo-backed orchestration for scheduled orbit and telemetry updates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from .database import propagate_and_store
from .telemetry import (
    detect_anomalies,
    simulate_telemetry,
    store_alerts,
    store_telemetry,
)


def run_once(
    database: Any,
    satellite_ids: Iterable[int] | None = None,
    timestamp: datetime | None = None,
    telemetry_seed: int | None = None,
    telemetry_faults: dict[int, str] | None = None,
) -> dict[str, int]:
    """
    Run one complete ORBIT-X processing cycle.

    For each satellite:

        MongoDB TLE
            ↓
        SGP4 propagation
            ↓
        orbital_states
            ↓
        telemetry simulation
            ↓
        anomaly detection
            ↓
        alerts

    A failure for one satellite does not stop the
    remaining satellites from being processed.

    Parameters
    ----------
    database:
        MongoDB database handle.

    satellite_ids:
        Optional iterable of NORAD IDs. If omitted,
        all satellites in the satellites collection
        are processed.

    timestamp:
        UTC timestamp for this processing cycle.

    telemetry_seed:
        Optional deterministic telemetry seed.

    telemetry_faults:
        Optional mapping:

            {
                25544: "LOW_BATTERY",
                20580: "HIGH_TEMPERATURE"
            }

        This is intended primarily for testing/demo
        anomaly detection.
    """

    timestamp = (
        timestamp
        or datetime.now(timezone.utc)
    )

    if timestamp.tzinfo is None:
        raise ValueError(
            "timestamp must include timezone information"
        )

    timestamp = timestamp.astimezone(
        timezone.utc
    )

    satellites = database["satellites"]

    orbital_states = database[
        "orbital_states"
    ]

    telemetry_collection = database[
        "telemetry"
    ]

    alerts_collection = database[
        "alerts"
    ]

    # ---------------------------------------------------------
    # Determine satellites to process
    # ---------------------------------------------------------

    if satellite_ids is None:

        satellite_ids = [
            document["norad_id"]
            for document in satellites.find(
                {},
                {"norad_id": 1}
            )
            if "norad_id" in document
        ]

    else:
        satellite_ids = list(satellite_ids)

    telemetry_faults = (
        telemetry_faults or {}
    )

    # ---------------------------------------------------------
    # Counters
    # ---------------------------------------------------------

    counts = {
        "satellites_requested": len(
            satellite_ids
        ),
        "satellites_processed": 0,
        "satellites_failed": 0,
        "orbital_states": 0,
        "telemetry": 0,
        "alerts": 0,
    }

    # ---------------------------------------------------------
    # Process each satellite independently
    # ---------------------------------------------------------

    for satellite_id in satellite_ids:

        try:

            # ---------------------------------------------
            # 1. SGP4 propagation
            # ---------------------------------------------

            propagate_and_store(
                satellites,
                orbital_states,
                satellite_id,
                timestamp,
            )

            counts["orbital_states"] += 1

            # ---------------------------------------------
            # 2. Telemetry simulation
            # ---------------------------------------------

            fault = telemetry_faults.get(
                satellite_id
            )

            telemetry = simulate_telemetry(
                satellite_id,
                timestamp,
                telemetry_seed,
                fault,
            )

            store_telemetry(
                telemetry_collection,
                telemetry,
            )

            counts["telemetry"] += 1

            # ---------------------------------------------
            # 3. Anomaly detection
            # ---------------------------------------------

            alerts = detect_anomalies(
                telemetry
            )

            counts["alerts"] += store_alerts(
                alerts_collection,
                alerts,
            )

            counts[
                "satellites_processed"
            ] += 1

        except Exception as error:

            counts[
                "satellites_failed"
            ] += 1

            print(
                f"[ERROR] ORBIT-X processing failed "
                f"for NORAD {satellite_id}: {error}"
            )

            # Continue processing the remaining
            # satellites.
            continue

    return counts