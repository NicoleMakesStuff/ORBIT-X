"""Mongo-backed orchestration for scheduled orbit and telemetry updates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from .database import propagate_and_store
from .telemetry import detect_anomalies, simulate_telemetry, store_alerts, store_telemetry


def run_once(
    database: Any,
    satellite_ids: Iterable[int] | None = None,
    timestamp: datetime | None = None,
    telemetry_seed: int | None = None,
) -> dict[str, int]:
    """Propagate and persist one cycle for selected or all satellites."""
    timestamp = timestamp or datetime.now(timezone.utc)
    satellites = database["satellites"]
    orbital_states = database["orbital_states"]
    telemetry_collection = database["telemetry"]
    alerts_collection = database["alerts"]

    if satellite_ids is None:
        satellite_ids = [
            document["norad_id"]
            for document in satellites.find({}, {"norad_id": 1})
            if "norad_id" in document
        ]

    counts = {"orbital_states": 0, "telemetry": 0, "alerts": 0}
    for satellite_id in satellite_ids:
        propagate_and_store(satellites, orbital_states, satellite_id, timestamp)
        counts["orbital_states"] += 1

        telemetry = simulate_telemetry(satellite_id, timestamp, telemetry_seed)
        store_telemetry(telemetry_collection, telemetry)
        counts["telemetry"] += 1
        alerts = detect_anomalies(telemetry)
        counts["alerts"] += store_alerts(alerts_collection, alerts)

    return counts