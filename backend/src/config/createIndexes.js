require("dotenv").config();

const mongoose = require("mongoose");

const createIndexes = async () => {

    try {

        await mongoose.connect(
            process.env.MONGODB_URI
        );

        const db = mongoose.connection.db;

        console.log("Connected to MongoDB");

        // --------------------------------
        // SATELLITES
        // --------------------------------

        await db.collection("satellites").createIndex(
            { norad_id: 1 },
            { unique: true }
        );

        await db.collection("satellites").createIndex(
            { status: 1 }
        );

        await db.collection("satellites").createIndex(
            { name: 1 }
        );

        // --------------------------------
        // MISSIONS
        // --------------------------------

        await db.collection("missions").createIndex(
            { mission_id: 1 },
            { unique: true }
        );

        await db.collection("missions").createIndex(
            { status: 1 }
        );

        // --------------------------------
        // TELEMETRY
        // --------------------------------

        await db.collection("telemetry").createIndex(
            {
                "metadata.satellite_id": 1,
                timestamp: -1
            }
        );

        // --------------------------------
        // ORBITAL STATES
        // --------------------------------

        await db.collection("orbital_states").createIndex(
            {
                "metadata.satellite_id": 1,
                timestamp: -1
            }
        );

        // --------------------------------
        // GROUND STATIONS
        // --------------------------------

        await db.collection("ground_stations").createIndex(
            {
                station_id: 1
            },
            {
                unique: true
            }
        );

        await db.collection("ground_stations").createIndex(
            {
                location: "2dsphere"
            }
        );

        // --------------------------------
        // COMMUNICATION EVENTS
        // --------------------------------

        await db.collection(
            "communication_events"
        ).createIndex({
            satellite_id: 1,
            start_time: -1
        });

        await db.collection(
            "communication_events"
        ).createIndex({
            ground_station_id: 1,
            start_time: -1
        });

        // --------------------------------
        // ALERTS
        // --------------------------------

        await db.collection("alerts").createIndex({
            satellite_id: 1,
            timestamp: -1
        });

        await db.collection("alerts").createIndex({
            severity: 1,
            timestamp: -1
        });

        console.log("All indexes created successfully");

        await mongoose.disconnect();

    } catch (error) {

        console.error(
            "Index creation failed:",
            error.message
        );

        process.exit(1);
    }
};

createIndexes();