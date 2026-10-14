# ORBIT-X
Orbit-Aware NoSQL Digital Twin and Predictive Health Monitoring Platform for Satellite Missions

## Mission-control dashboard

A responsive ORBIT-X dashboard is included in `frontend/index.html`. It is served by the existing Express backend, so no separate frontend build or extra npm dependencies are required.

1. Configure the root `.env` with `MONGODB_URI`, `MONGODB_DB_NAME=orbit_x`, and optionally `PORT=5000`.
2. From `backend/`, install dependencies with `npm install` if you have not already done so.
3. Start the backend with `npm start`.
4. Open **http://localhost:5000/dashboard**.

The dashboard reads the existing REST endpoints for summary, satellites, orbital states, telemetry, alerts, missions, ground stations, and communication events. The top-right status indicates whether it is reading from the live API or using clearly labelled demo fallback data. Refresh is available in the header; the dashboard also refreshes automatically every 60 seconds when the API is connected. Alert acknowledgement is persisted only when MongoDB is connected and the alert exists in the database.

Scope note: the orbital illustration is a mission-control visual, not a precision 3D globe or map. Telemetry is simulated by the current Python engine and anomaly detection is threshold-based; the dashboard does not claim live spacecraft telemetry or trained predictive ML.


### Orbit Prediction dashboard

Open `http://localhost:5000/dashboard/` while the backend is running. Select a satellite with a complete stored TLE, choose a `+5`, `+15`, `+30`, or `+60 minute` horizon, and click **Calculate prediction**. The dashboard calls `GET /api/satellites/:noradId/prediction?minutes=15`, which invokes the existing Python SGP4 propagator and returns a current position, selected future position, and minute-by-minute ground-track samples. The calculation is performed on demand and is not persisted as orbital history.

The backend invokes Python using `PYTHON_EXECUTABLE` if set, otherwise `python` on Windows or `python3` on other platforms. Ensure the selected interpreter has the packages in `ai/requirements.txt` installed. For example, set `PYTHON_EXECUTABLE` in the backend environment if the backend and Python engine use different interpreters. The interactive map loads Leaflet and OpenStreetMap tiles from the internet.

**Accuracy note:** the current project uses an approximate TEME-to-ECEF conversion for visualization/basic tracking, not high-precision navigation. Prediction quality also depends on the TLE epoch/freshness.
