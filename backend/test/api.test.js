const assert = require("node:assert/strict");
const http = require("node:http");
const test = require("node:test");

const app = require("../src/app");

const request = (server, path, method = "GET", payload) => new Promise((resolve, reject) => {
    const { port } = server.address();
    const body = payload ? JSON.stringify(payload) : "";
    const requestOptions = {
        method,
        host: "127.0.0.1",
        port,
        path,
        headers: payload ? {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(body)
        } : undefined
    };
    const clientRequest = http.request(requestOptions, (response) => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
            body += chunk;
        });
        response.on("end", () => {
            resolve({ status: response.statusCode, body: JSON.parse(body) });
        });
    });
    clientRequest.on("error", reject);
    if (payload) {
        clientRequest.write(body);
    }
    clientRequest.end();
});

test("Person 3 API validates requests without a database connection", async () => {
    const server = app.listen(0);
    try {
        const health = await request(server, "/api/health");
        assert.equal(health.status, 200);
        assert.equal(health.body.status, "online");

        const readiness = await request(server, "/api/health/ready");
        assert.equal(readiness.status, 503);
        assert.equal(readiness.body.status, "not_ready");

        const docs = await request(server, "/api/docs");
        assert.equal(docs.status, 200);
        assert.ok(docs.body.endpoints.operations.includes("GET /api/summary"));

        const invalidSatellite = await request(server, "/api/satellites/not-a-number");
        assert.equal(invalidSatellite.status, 400);

        const invalidEvents = await request(server, "/api/communication-events?satelliteId=bad");
        assert.equal(invalidEvents.status, 400);

        const invalidLimit = await request(server, "/api/satellites?limit=20junk");
        assert.equal(invalidLimit.status, 400);

        const invalidSeverity = await request(server, "/api/alerts?severity=urgent");
        assert.equal(invalidSeverity.status, 400);

        const invalidStation = await request(server, "/api/ground-stations/%20");
        assert.equal(invalidStation.status, 400);

        const invalidAlert = await request(
            server,
            "/api/alerts/ALERT-1",
            "PATCH",
            { acknowledgement: "INVALID" }
        );
        assert.equal(invalidAlert.status, 400);

        const missingRoute = await request(server, "/api/not-a-route");
        assert.equal(missingRoute.status, 404);
        assert.equal(missingRoute.body.error, "Route not found");
    } finally {
        await new Promise((resolve) => server.close(resolve));
    }
});