const mongoose = require("mongoose");

const telemetrySchema = new mongoose.Schema(
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

        power: {
            battery_percent: Number,
            voltage: Number,
            current: Number
        },

        thermal: {
            cpu_temperature: Number,
            payload_temperature: Number
        },

        communication: {
            rssi: Number,
            packet_loss: Number
        },

        attitude: {
            roll: Number,
            pitch: Number,
            yaw: Number
        },

        system: {
            cpu_load: Number,
            memory_usage: Number
        },

        mission: {
            mode: String,
            payload_active: Boolean
        }
    },
    {
        collection: "telemetry"
    }
);

module.exports = mongoose.model(
    "Telemetry",
    telemetrySchema
);