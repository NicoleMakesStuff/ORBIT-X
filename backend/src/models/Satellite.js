const mongoose = require("mongoose");

const sensorSchema = new mongoose.Schema(
    {
        type: {
            type: String,
            required: true
        },

        status: {
            type: String,
            enum: [
                "ONLINE",
                "OFFLINE",
                "DEGRADED",
                "UNKNOWN"
            ],
            default: "UNKNOWN"
        }
    },
    { _id: false }
);

const satelliteSchema = new mongoose.Schema(
    {
        norad_id: {
            type: Number,
            required: true,
            unique: true,
            index: true
        },

        name: {
            type: String,
            required: true,
            index: true
        },

        international_designator: {
            type: String
        },

        status: {
            type: String,
            enum: [
                "ACTIVE",
                "INACTIVE",
                "DECOMMISSIONED",
                "UNKNOWN"
            ],
            default: "UNKNOWN",
            index: true
        },

        mission_id: {
            type: String,
            index: true
        },

        mission: {
            id: String,
            name: String
        },

        operators: {
            type: [String],
            default: []
        },

        sensors: {
            type: [sensorSchema],
            default: []
        },

        tle: {
            line1: String,
            line2: String,
            epoch: Date,
            source: String
        }
    },
    {
        timestamps: true,
        collection: "satellites"
    }
);

module.exports = mongoose.model("Satellite", satelliteSchema);