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
) -> dict[str, Any]:
    timestamp = timestamp or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must include timezone information")
    generator = random.Random(seed)
    return {
        "timestamp": timestamp.astimezone(timezone.utc),
        "metadata": {"satellite_id": satellite_id},
        "power": {
            "battery_percent": round(generator.uniform(70, 98), 2),
            "voltage": round(generator.uniform(7.4, 8.2), 3),
            "current": round(generator.uniform(0.4, 1.8), 3),
        },
        "thermal": {
            "cpu_temperature": round(generator.uniform(18, 55), 2),
            "payload_temperature": round(generator.uniform(10, 45), 2),
        },
        "communication": {
            "rssi": round(generator.uniform(-85, -55), 2),
            "packet_loss": round(generator.uniform(0, 4), 2),
        },
        "attitude": {
            "roll": round(generator.uniform(-5, 5), 3),
            "pitch": round(generator.uniform(-5, 5), 3),
            "yaw": round(generator.uniform(0, 360), 3),
        },
        "system": {
            "cpu_load": round(generator.uniform(15, 75), 2),
            "memory_usage": round(generator.uniform(20, 80), 2),
        },
        "mission": {"mode": "NOMINAL", "payload_active": True},
    }


def detect_anomalies(telemetry: dict[str, Any]) -> list[dict[str, Any]]:
    satellite_id = telemetry["metadata"]["satellite_id"]
    timestamp = telemetry["timestamp"]
    checks = [
        ("power.battery_percent", telemetry["power"]["battery_percent"], 20, "LOW", "Battery below 20%"),
        ("power.voltage", telemetry["power"]["voltage"], 6.5, "HIGH", "Voltage below 6.5 V"),
        ("thermal.cpu_temperature", telemetry["thermal"]["cpu_temperature"], 70, "HIGH", "CPU temperature above 70 C"),
        ("communication.packet_loss", telemetry["communication"]["packet_loss"], 10, "MEDIUM", "Packet loss above 10%"),
    ]
    alerts = []
    for parameter, value, threshold, severity, explanation in checks:
        is_low_battery = parameter == "power.battery_percent"
        violated = value < threshold if is_low_battery or parameter == "power.voltage" else value > threshold
        if violated:
            alerts.append({
                "alert_id": f"{satellite_id}-{parameter}-{timestamp.isoformat()}",
                "satellite_id": satellite_id,
                "timestamp": timestamp,
                "severity": severity,
                "parameter": parameter,
                "current_value": value,
                "expected_value": f">= {threshold}" if is_low_battery or parameter == "power.voltage" else f"<= {threshold}",
                "anomaly_score": 1.0,
                "explanation": explanation,
                "acknowledgement": "UNACKNOWLEDGED",
            })
    return alerts


def store_telemetry(telemetry_collection: Collection, telemetry: dict[str, Any]) -> Any:
    """Insert one telemetry sample into the schema used by the Node backend."""
    return telemetry_collection.insert_one(telemetry).inserted_id


def store_alerts(alert_collection: Collection, alerts: list[dict[str, Any]]) -> int:
    """Persist generated alerts and return the number inserted."""
    if not alerts:
        return 0
    return len(alert_collection.insert_many(alerts).inserted_ids)