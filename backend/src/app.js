const express = require("express");
const cors = require("cors");
const path = require("path");
const { spawn } = require("child_process");

const Satellite = require("./models/Satellite");
const OrbitalState = require("./models/OrbitalState");
const Telemetry = require("./models/Telemetry");
const Alert = require("./models/Alert");
const Mission = require("./models/Mission");
const GroundStation = require("./models/GroundStation");
const CommunicationEvent = require("./models/CommunicationEvent");

const app = express();

const ACKNOWLEDGEMENT_STATES = [
    "UNACKNOWLEDGED",
    "ACKNOWLEDGED",
    "RESOLVED"
];
const SEVERITY_STATES = Alert.schema.path("severity").enumValues;

app.use(cors());
app.use(express.json());

// Serve the ORBIT-X mission-control dashboard without a separate frontend build.
app.use("/dashboard", express.static(path.resolve(__dirname, "../../frontend")));

const parseLimit = (value) => {
    const rawValue = value === undefined ? "20" : `${value}`;
    if (!/^\d+$/.test(rawValue)) {
        const error = new Error("limit must be an integer between 1 and 100");
        error.status = 400;
        throw error;
    }
    const limit = Number(rawValue);
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
        const error = new Error("limit must be an integer between 1 and 100");
        error.status = 400;
        throw error;
    }
    return limit;
};

const parseNoradId = (value) => {
    if (!/^\d+$/.test(`${value}`)) {
        const error = new Error("noradId must be a positive integer");
        error.status = 400;
        throw error;
    }
    const noradId = Number(value);
    if (!Number.isInteger(noradId) || noradId < 1) {
        const error = new Error("noradId must be a positive integer");
        error.status = 400;
        throw error;
    }
    return noradId;
};

const parseRequiredString = (value, field) => {
    if (typeof value !== "string" || value.trim() === "") {
        const error = new Error(`${field} is required`);
        error.status = 400;
        throw error;
    }
    return value.trim();
};

app.get("/", (req, res) => {
    res.json({
        project: "ORBIT-X",
        status: "online"
    });
});

app.get("/api/health", (req, res) => {
    res.json({
        status: "online",
        database: OrbitalState.db.readyState === 1 ? "connected" : "disconnected"
    });
});

app.get("/api/health/ready", (req, res) => {
    const ready = OrbitalState.db.readyState === 1;
    res.status(ready ? 200 : 503).json({
        status: ready ? "ready" : "not_ready",
        database: ready ? "connected" : "disconnected"
    });
});

app.get("/api/docs", (req, res) => {
    res.json({
        name: "ORBIT-X API",
        version: "1.0.0",
        endpoints: {
            health: ["GET /api/health", "GET /api/health/ready"],
            satellites: [
                "GET /api/satellites",
                "GET /api/satellites/:noradId",
                "GET /api/satellites/:noradId/orbital-states",
                "GET /api/satellites/:noradId/prediction?minutes=5|15|30|60",
                "GET /api/satellites/:noradId/telemetry",
                "GET /api/satellites/:noradId/alerts"
            ],
            operations: [
                "GET /api/summary",
                "GET /api/missions",
                "GET /api/ground-stations",
                "GET /api/ground-stations/:stationId",
                "GET /api/communication-events",
                "GET /api/alerts",
                "PATCH /api/alerts/:alertId"
            ]
        },
        pagination: "Use limit=1..100 on collection endpoints."
    });
});

app.get("/api/satellites", async (req, res, next) => {
    try {
        const limit = parseLimit(req.query.limit);
        const satellites = await Satellite.find({})
            .sort({ name: 1 })
            .limit(limit)
            .lean();
        res.json({ data: satellites, count: satellites.length });
    } catch (error) {
        next(error);
    }
});

app.get("/api/satellites/:noradId", async (req, res, next) => {
    try {
        const satellite = await Satellite.findOne({
            norad_id: parseNoradId(req.params.noradId)
        }).lean();
        if (!satellite) {
            return res.status(404).json({ error: "Satellite not found" });
        }
        res.json({ data: satellite });
    } catch (error) {
        next(error);
    }
});

const historyEndpoint = (Model, field) => async (req, res, next) => {
    try {
        const satelliteId = parseNoradId(req.params.noradId);
        const limit = parseLimit(req.query.limit);
        const filter = field === "metadata.satellite_id"
            ? { "metadata.satellite_id": satelliteId }
            : { satellite_id: satelliteId };
        const records = await Model.find(filter)
            .sort({ timestamp: -1 })
            .limit(limit)
            .lean();
        res.json({ data: records, count: records.length });
    } catch (error) {
        next(error);
    }
};

app.get(
    "/api/satellites/:noradId/orbital-states",
    historyEndpoint(OrbitalState, "metadata.satellite_id")
);

// Calculate a real current/future position and ground track from the stored TLE.
// Python's existing SGP4 implementation is reused; results are calculated on
// demand and are not inserted into orbital_states.
app.get("/api/satellites/:noradId/prediction", async (req, res, next) => {
    try {
        const noradId = parseNoradId(req.params.noradId);
        const minutes = Number(req.query.minutes === undefined ? 15 : req.query.minutes);
        if (![5, 15, 30, 60].includes(minutes)) {
            return res.status(400).json({ error: "minutes must be one of 5, 15, 30, or 60" });
        }

        const satellite = await Satellite.findOne({ norad_id: noradId }).lean();
        if (!satellite) {
            return res.status(404).json({ error: "Satellite not found" });
        }
        if (!satellite.tle || !satellite.tle.line1 || !satellite.tle.line2) {
            return res.status(422).json({ error: "Satellite has no complete TLE. Run satellite ingestion first." });
        }

        const projectRoot = path.resolve(__dirname, "../../");
        const scriptPath = path.join(projectRoot, "ai", "orbit", "predict_orbit_cli.py");
        const pythonExecutable = process.env.PYTHON_EXECUTABLE || (process.platform === "win32" ? "python" : "python3");
        const child = spawn(pythonExecutable, [scriptPath], {
            cwd: projectRoot,
            env: {
                ...process.env,
                PYTHONPATH: [path.join(projectRoot, "ai"), process.env.PYTHONPATH || ""].filter(Boolean).join(path.delimiter)
            },
            stdio: ["pipe", "pipe", "pipe"]
        });

        let stdout = "";
        let stderr = "";
        child.stdout.setEncoding("utf8");
        child.stderr.setEncoding("utf8");
        child.stdout.on("data", chunk => { stdout += chunk; });
        child.stderr.on("data", chunk => { stderr += chunk; });
        child.on("error", error => {
            if (!res.headersSent) res.status(503).json({ error: `Could not start Python (${pythonExecutable}). Set PYTHON_EXECUTABLE if needed.`, detail: error.message });
        });
        child.on("close", code => {
            if (res.headersSent) return;
            let result;
            try { result = JSON.parse(stdout); }
            catch { return res.status(502).json({ error: "Orbit prediction returned invalid output", detail: stderr.slice(0, 500) }); }
            if (code !== 0 || result.error) {
                return res.status(422).json({ error: result.error || "Orbit propagation failed", detail: stderr.slice(0, 500) });
            }
            result.satellite = { norad_id: satellite.norad_id, name: satellite.name, tle_epoch: satellite.tle.epoch || result.current.tle_epoch, tle_source: satellite.tle.source || "Stored TLE" };
            res.json({ data: result });
        });
        child.stdin.end(JSON.stringify({
            satellite_id: noradId,
            line1: satellite.tle.line1,
            line2: satellite.tle.line2,
            timestamp: new Date().toISOString(),
            minutes
        }));
    } catch (error) {
        next(error);
    }
});
app.get(
    "/api/satellites/:noradId/telemetry",
    historyEndpoint(Telemetry, "metadata.satellite_id")
);
app.get(
    "/api/satellites/:noradId/alerts",
    historyEndpoint(Alert, "satellite_id")
);

app.get("/api/missions", async (req, res, next) => {
    try {
        const limit = parseLimit(req.query.limit);
        const missions = await Mission.find({})
            .sort({ name: 1 })
            .limit(limit)
            .lean();
        res.json({ data: missions, count: missions.length });
    } catch (error) {
        next(error);
    }
});

app.get("/api/ground-stations", async (req, res, next) => {
    try {
        const limit = parseLimit(req.query.limit);
        const stations = await GroundStation.find({})
            .sort({ name: 1 })
            .limit(limit)
            .lean();
        res.json({ data: stations, count: stations.length });
    } catch (error) {
        next(error);
    }
});

app.get("/api/ground-stations/:stationId", async (req, res, next) => {
    try {
        const station = await GroundStation.findOne({
            station_id: parseRequiredString(req.params.stationId, "stationId")
        }).lean();
        if (!station) {
            return res.status(404).json({ error: "Ground station not found" });
        }
        res.json({ data: station });
    } catch (error) {
        next(error);
    }
});

app.get("/api/communication-events", async (req, res, next) => {
    try {
        const limit = parseLimit(req.query.limit);
        const filter = {};
        if (req.query.satelliteId !== undefined) {
            filter.satellite_id = parseNoradId(req.query.satelliteId);
        }
        if (req.query.stationId !== undefined) {
            filter.ground_station_id = parseRequiredString(req.query.stationId, "stationId");
        }
        const events = await CommunicationEvent.find(filter)
            .sort({ start_time: -1 })
            .limit(limit)
            .lean();
        res.json({ data: events, count: events.length });
    } catch (error) {
        next(error);
    }
});

app.get("/api/alerts", async (req, res, next) => {
    try {
        const limit = parseLimit(req.query.limit);
        const filter = {};
        if (req.query.satelliteId !== undefined) {
            filter.satellite_id = parseNoradId(req.query.satelliteId);
        }
        if (req.query.severity !== undefined) {
            const severity = parseRequiredString(req.query.severity, "severity").toUpperCase();
            if (!SEVERITY_STATES.includes(severity)) {
                const error = new Error("invalid severity");
                error.status = 400;
                throw error;
            }
            filter.severity = severity;
        }
        if (req.query.acknowledgement !== undefined) {
            const acknowledgement = parseRequiredString(
                req.query.acknowledgement,
                "acknowledgement"
            ).toUpperCase();
            if (!ACKNOWLEDGEMENT_STATES.includes(acknowledgement)) {
                const error = new Error("invalid acknowledgement state");
                error.status = 400;
                throw error;
            }
            filter.acknowledgement = acknowledgement;
        }
        const alerts = await Alert.find(filter)
            .sort({ timestamp: -1 })
            .limit(limit)
            .lean();
        res.json({ data: alerts, count: alerts.length });
    } catch (error) {
        next(error);
    }
});

app.patch("/api/alerts/:alertId", async (req, res, next) => {
    try {
        const alertId = parseRequiredString(req.params.alertId, "alertId");
        const acknowledgement = parseRequiredString(
            req.body && req.body.acknowledgement,
            "acknowledgement"
        ).toUpperCase();
        if (!ACKNOWLEDGEMENT_STATES.includes(acknowledgement)) {
            const error = new Error("invalid acknowledgement state");
            error.status = 400;
            throw error;
        }
        const alert = await Alert.findOneAndUpdate(
            { alert_id: alertId },
            { acknowledgement },
            { new: true, runValidators: true }
        ).lean();
        if (!alert) {
            return res.status(404).json({ error: "Alert not found" });
        }
        res.json({ data: alert });
    } catch (error) {
        next(error);
    }
});

app.get("/api/summary", async (req, res, next) => {
    try {
        const [satellites, missions, groundStations, activeAlerts, latestStates] =
            await Promise.all([
                Satellite.countDocuments({}),
                Mission.countDocuments({}),
                GroundStation.countDocuments({ status: "ONLINE" }),
                Alert.countDocuments({ acknowledgement: "UNACKNOWLEDGED" }),
                OrbitalState.find({})
                    .sort({ timestamp: -1 })
                    .limit(10)
                    .select({ _id: 0, metadata: 1, timestamp: 1, position: 1 })
                    .lean()
            ]);
        res.json({
            data: { satellites, missions, online_ground_stations: groundStations, active_alerts: activeAlerts, latest_states: latestStates }
        });
    } catch (error) {
        next(error);
    }
});

app.use((req, res) => {
    res.status(404).json({ error: "Route not found" });
});

app.use((error, req, res, next) => {
    const status = error.status || 500;
    res.status(status).json({
        error: status === 500 ? "Internal server error" : error.message
    });
});

module.exports = app;