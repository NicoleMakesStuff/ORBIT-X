require("dotenv").config();

const mongoose = require("mongoose");

const setupDatabase = async () => {
    try {
        await mongoose.connect(process.env.MONGODB_URI);

        console.log("Connected to MongoDB");

        const db = mongoose.connection.db;

        // --------------------------------
        // TELEMETRY
        // --------------------------------

        const telemetryExists =
            await db.listCollections({
                name: "telemetry"
            }).hasNext();

        if (!telemetryExists) {
            await db.createCollection("telemetry", {
                timeseries: {
                    timeField: "timestamp",
                    metaField: "metadata",
                    granularity: "seconds"
                }
            });

            console.log(
                "Created telemetry time-series collection"
            );
        }

        // --------------------------------
        // ORBITAL STATES
        // --------------------------------

        const orbitalExists =
            await db.listCollections({
                name: "orbital_states"
            }).hasNext();

        if (!orbitalExists) {
            await db.createCollection("orbital_states", {
                timeseries: {
                    timeField: "timestamp",
                    metaField: "metadata",
                    granularity: "seconds"
                }
            });

            console.log(
                "Created orbital_states time-series collection"
            );
        }

        // --------------------------------
        // NORMAL COLLECTIONS
        // --------------------------------

        const collections = [
            "satellites",
            "missions",
            "ground_stations",
            "communication_events",
            "alerts"
        ];

        for (const collection of collections) {
            const exists =
                await db.listCollections({
                    name: collection
                }).hasNext();

            if (!exists) {
                await db.createCollection(collection);

                console.log(
                    `Created ${collection} collection`
                );
            }
        }

        console.log("Database setup complete");

        await mongoose.disconnect();

    } catch (error) {
        console.error(
            "Database setup failed:",
            error.message
        );

        process.exit(1);
    }
};

setupDatabase();