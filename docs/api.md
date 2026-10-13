# ORBIT-X API

The backend serves JSON under `/api`. Start it from `backend/` with `npm start`.

## Health and discovery

- `GET /api/health` returns process status and current MongoDB connection state.
- `GET /api/health/ready` returns `200` only when MongoDB is connected; otherwise it returns `503`.
- `GET /api/docs` returns the endpoint list and pagination rules.
- `GET /api/summary` returns dashboard counts and the latest orbital states.

## Satellite operations

- `GET /api/satellites?limit=20`
- `GET /api/satellites/:noradId`
- `GET /api/satellites/:noradId/orbital-states?limit=20`
- `GET /api/satellites/:noradId/telemetry?limit=20`
- `GET /api/satellites/:noradId/alerts?limit=20`

## Mission and ground operations

- `GET /api/missions?limit=20`
- `GET /api/ground-stations?limit=20`
- `GET /api/ground-stations/:stationId`
- `GET /api/communication-events?limit=20&satelliteId=25544&stationId=GS-001`

## Alert operations

- `GET /api/alerts?limit=20&satelliteId=25544&severity=HIGH&acknowledgement=UNACKNOWLEDGED`
- `PATCH /api/alerts/:alertId` with body `{ "acknowledgement": "ACKNOWLEDGED" }`

Allowed acknowledgement states are `UNACKNOWLEDGED`, `ACKNOWLEDGED`, and `RESOLVED`.
Collection endpoints accept `limit` from `1` through `100` and return `{ data, count }`.