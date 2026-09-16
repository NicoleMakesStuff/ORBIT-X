require("dotenv").config();

const mongoose = require("mongoose");

const seedDatabase = async () => {
    try {
        await mongoose.connect(process.env.MONGODB_URI);

        const db = mongoose.connection.db;

        console.log("Connected to MongoDB");

        // ------------------------------------
        // MISSION
        // ------------------------------------

        await db.collection("missions").updateOne(
            { mission_id: "ORBIT-X-DEMO" },
            {
                $set: {
                    mission_id: "ORBIT-X-DEMO",
                    name: "ORBIT-X Demonstration Mission",
                    description:
                        "Demonstration mission for the ORBIT-X satellite digital twin.",
                    mission_type: "EARTH_OBSERVATION",
                    operator: "ORBIT-X",
                    status: "ACTIVE",
                    start_date: new Date()
                }
            },
            { upsert: true }
        );

        // ------------------------------------
        // SATELLITE
        // ------------------------------------

        await db.collection("satellites").updateOne(
            { norad_id: 99999 },
            {
                $set: {
                    norad_id: 99999,
                    name: "ORBIT-X-DEMO",
                    international_designator: "2026-ORBX",
                    status: "ACTIVE",

                    mission_id: "ORBIT-X-DEMO",

                    mission: {
                        id: "ORBIT-X-DEMO",
                        name: "ORBIT-X Demonstration Mission"
                    },

                    operators: [
                        "ORBIT-X"
                    ],

                    sensors: [
                        {
                            type: "temperature",
                            status: "ONLINE"
                        },
                        {
                            type: "IMU",
                            status: "ONLINE"
                        },
                        {
                            type: "GPS",
                            status: "ONLINE"
                        }
                    ]
                }
            },
            { upsert: true }
        );

        // ------------------------------------
        // GROUND STATION
        // ------------------------------------

        await db.collection("ground_stations").updateOne(
            { station_id: "GS-001" },
            {
                $set: {
                    station_id: "GS-001",
                    name: "Vellore Ground Station",

                    location: {
                        type: "Point",
                        coordinates: [
                            79.1637,
                            12.9692
                        ]
                    },

                    antennas: [
                        {
                            band: "UHF",
                            frequency_mhz: 437.5,
                            status: "ACTIVE"
                        },
                        {
                            band: "S-BAND",
                            frequency_mhz: 2200,
                            status: "ACTIVE"
                        }
                    ],

                    status: "ONLINE"
                }
            },
            { upsert: true }
        );

        // ------------------------------------
        // ALERT
        // ------------------------------------

        await db.collection("alerts").updateOne(
            { alert_id: "ORBX-TEST-001" },
            {
                $set: {
                    alert_id: "ORBX-TEST-001",
                    satellite_id: 99999,
                    timestamp: new Date(),

                    severity: "INFO",

                    parameter: "SYSTEM",

                    current_value: "Database test",
                    expected_value: "Database operational",

                    anomaly_score: 0,

                    explanation:
                        "Test alert used to verify ORBIT-X database connectivity.",

                    acknowledgement: "UNACKNOWLEDGED"
                }
            },
            { upsert: true }
        );

        console.log("Test documents inserted successfully");

        await mongoose.disconnect();

    } catch (error) {

        console.error(
            "Database seeding failed:",
            error.message
        );

        process.exit(1);
    }
};

seedDatabase();