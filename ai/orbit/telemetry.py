"""Deterministic telemetry simulation and threshold-based anomaly detection."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection


def simulate_telemetry(
    satellite_id: int,
    timestamp: datetime | None = None,
    seed: int | None = None,
    fault: str | None = None,
) -> dict[str, Any]:
    """
    Generate deterministic simulated satellite telemetry.

    Parameters
    ----------
    satellite_id:
        NORAD ID of the satellite.

    timestamp:
        UTC timestamp for the telemetry sample.

    seed:
        Optional random seed. Using the same seed produces
        repeatable telemetry.

    fault:
        Optional deterministic fault injection.

        Supported faults:

        LOW_BATTERY
        LOW_VOLTAGE
        HIGH_TEMPERATURE
        HIGH_PACKET_LOSS
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

    generator = random.Random(seed)

    telemetry: dict[str, Any] = {
        "timestamp": timestamp,

        "metadata": {
            "satellite_id": satellite_id,
        },

        "power": {
            "battery_percent": round(
                generator.uniform(70, 98),
                2,
            ),
            "voltage": round(
                generator.uniform(7.4, 8.2),
                3,
            ),
            "current": round(
                generator.uniform(0.4, 1.8),
                3,
            ),
        },

        "thermal": {
            "cpu_temperature": round(
                generator.uniform(18, 55),
                2,
            ),
            "payload_temperature": round(
                generator.uniform(10, 45),
                2,
            ),
        },

        "communication": {
            "rssi": round(
                generator.uniform(-85, -55),
                2,
            ),
            "packet_loss": round(
                generator.uniform(0, 4),
                2,
            ),
        },

        "attitude": {
            "roll": round(
                generator.uniform(-5, 5),
                3,
            ),
            "pitch": round(
                generator.uniform(-5, 5),
                3,
            ),
            "yaw": round(
                generator.uniform(0, 360),
                3,
            ),
        },

        "system": {
            "cpu_load": round(
                generator.uniform(15, 75),
                2,
            ),
            "memory_usage": round(
                generator.uniform(20, 80),
                2,
            ),
        },

        "mission": {
            "mode": "NOMINAL",
            "payload_active": True,
        },
    }

    # ---------------------------------------------------------
    # Deterministic fault injection
    # ---------------------------------------------------------

    if fault == "LOW_BATTERY":
        telemetry["power"]["battery_percent"] = 10

    elif fault == "LOW_VOLTAGE":
        telemetry["power"]["voltage"] = 5.8

    elif fault == "HIGH_TEMPERATURE":
        telemetry["thermal"]["cpu_temperature"] = 85

    elif fault == "HIGH_PACKET_LOSS":
        telemetry["communication"]["packet_loss"] = 25

    elif fault is not None:
        raise ValueError(
            f"unsupported telemetry fault: {fault}"
        )

    return telemetry


def detect_anomalies(
    telemetry: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Check telemetry against predefined thresholds
    and generate alert documents.
    """

    satellite_id = telemetry["metadata"]["satellite_id"]

    timestamp = telemetry["timestamp"]

    checks = [
        (
            "power.battery_percent",
            telemetry["power"]["battery_percent"],
            20,
            "LOW",
            "Battery below 20%",
        ),
        (
            "power.voltage",
            telemetry["power"]["voltage"],
            6.5,
            "HIGH",
            "Voltage below 6.5 V",
        ),
        (
            "thermal.cpu_temperature",
            telemetry["thermal"]["cpu_temperature"],
            70,
            "HIGH",
            "CPU temperature above 70 C",
        ),
        (
            "communication.packet_loss",
            telemetry["communication"]["packet_loss"],
            10,
            "MEDIUM",
            "Packet loss above 10%",
        ),
    ]

    alerts: list[dict[str, Any]] = []

    for (
        parameter,
        value,
        threshold,
        severity,
        explanation,
    ) in checks:

        is_low_threshold = (
            parameter == "power.battery_percent"
            or parameter == "power.voltage"
        )

        violated = (
            value < threshold
            if is_low_threshold
            else value > threshold
        )

        if not violated:
            continue

        if is_low_threshold:
            expected_value = f">= {threshold}"
        else:
            expected_value = f"<= {threshold}"

        alert = {
            "alert_id": (
                f"{satellite_id}-"
                f"{parameter}-"
                f"{timestamp.isoformat()}"
            ),

            "satellite_id": satellite_id,

            "timestamp": timestamp,

            "severity": severity,

            "parameter": parameter,

            "current_value": value,

            "expected_value": expected_value,

            "anomaly_score": 1.0,

            "explanation": explanation,

            "acknowledgement": "UNACKNOWLEDGED",
        }

        alerts.append(alert)

    return alerts


def store_telemetry(
    telemetry_collection: Collection,
    telemetry: dict[str, Any],
) -> Any:
    """
    Insert one telemetry sample.

    Telemetry is stored in the ORBIT-X time-series
    telemetry collection.
    """

    return telemetry_collection.insert_one(
        telemetry
    ).inserted_id


def store_alerts(
    alert_collection: Collection,
    alerts: list[dict[str, Any]],
) -> int:
    """
    Store alerts idempotently.

    Existing alert_id values are not inserted again.

    Returns the number of newly inserted alerts.
    """

    if not alerts:
        return 0

    inserted = 0

    for alert in alerts:

        result = alert_collection.update_one(
            {
                "alert_id": alert["alert_id"]
            },
            {
                "$setOnInsert": alert
            },
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1

    return inserted