"""JSON-in/JSON-out adapter for the ORBIT-X SGP4 propagation module.

This script is invoked by the Express prediction endpoint. It does not write
anything to MongoDB; it calculates a current state and a future ground track
from the satellite's stored TLE.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

from propagation import propagate_tle


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone information")
    return parsed.astimezone(timezone.utc)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        satellite_id = int(payload["satellite_id"])
        line1 = str(payload["line1"]).strip()
        line2 = str(payload["line2"]).strip()
        start = parse_timestamp(payload["timestamp"])
        horizon = int(payload["minutes"])
        if horizon not in (5, 15, 30, 60):
            raise ValueError("minutes must be one of 5, 15, 30, or 60")
        if not line1 or not line2:
            raise ValueError("satellite TLE is incomplete")

        def state_at(when: datetime) -> dict:
            result = propagate_tle(satellite_id, line1, line2, when)
            result["timestamp"] = result["timestamp"].isoformat()
            result["tle_epoch"] = result["tle_epoch"].isoformat()
            return result

        current = state_at(start)
        track = []
        for minute in range(0, horizon + 1):
            track.append(state_at(start + timedelta(minutes=minute)))
        prediction = track[-1]

        response = {
            "satellite_id": satellite_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "requested_minutes": horizon,
            "propagation_method": "SGP4",
            "source": "Calculated from stored TLE using the ORBIT-X SGP4 propagator",
            "coordinate_note": "Geodetic coordinates use the project's approximate TEME-to-ECEF GMST conversion; suitable for visualization/basic tracking, not high-precision navigation.",
            "current": current,
            "prediction": prediction,
            "ground_track": track,
        }
        print(json.dumps(response, separators=(",", ":")))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stdout)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
