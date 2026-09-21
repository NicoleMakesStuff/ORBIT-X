const mongoose = require("mongoose");

const orbitalStateSchema = new mongoose.Schema(
    {
        timestamp: {
            type: Date,
            required: true
        },

        metadata: {
            satellite_id: {
                type: Number,
                required: true
            }
        },

        position: {
            latitude: Number,
            longitude: Number,
            altitude_km: Number
        },

        velocity: {
            x_km_s: Number,
            y_km_s: Number,
            z_km_s: Number
        },

        propagation_method: {
            type: String,
            default: "SGP4"
        },

        tle_epoch: Date,

        orbital: {
            inclination_deg: Number,
            period_minutes: Number,
            phase: String
        },

        eclipse: Boolean
    },
    {
        collection: "orbital_states"
    }
);

module.exports = mongoose.model(
    "OrbitalState",
    orbitalStateSchema
);