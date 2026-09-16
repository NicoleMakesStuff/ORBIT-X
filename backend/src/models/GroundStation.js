const mongoose = require("mongoose");

const antennaSchema = new mongoose.Schema(
    {
        band: {
            type: String,
            required: true
        },

        frequency_mhz: {
            type: Number,
            required: true
        },

        status: {
            type: String,
            enum: [
                "ACTIVE",
                "INACTIVE",
                "MAINTENANCE"
            ],
            default: "ACTIVE"
        }
    },
    { _id: false }
);

const groundStationSchema = new mongoose.Schema(
    {
        station_id: {
            type: String,
            required: true,
            unique: true,
            index: true
        },

        name: {
            type: String,
            required: true
        },

        location: {
            type: {
                type: String,
                enum: ["Point"],
                required: true
            },

            coordinates: {
                type: [Number],
                required: true
            }
        },

        antennas: {
            type: [antennaSchema],
            default: []
        },

        status: {
            type: String,
            enum: [
                "ONLINE",
                "OFFLINE",
                "MAINTENANCE"
            ],
            default: "ONLINE",
            index: true
        }
    },
    {
        timestamps: true,
        collection: "ground_stations"
    }
);

groundStationSchema.index({
    location: "2dsphere"
});

module.exports = mongoose.model(
    "GroundStation",
    groundStationSchema
);