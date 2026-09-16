const mongoose = require("mongoose");

const alertSchema = new mongoose.Schema(
    {
        alert_id: {
            type: String,
            required: true,
            unique: true,
            index: true
        },

        satellite_id: {
            type: Number,
            required: true,
            index: true
        },

        timestamp: {
            type: Date,
            required: true,
            index: true
        },

        severity: {
            type: String,
            enum: [
                "INFO",
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL"
            ],
            required: true,
            index: true
        },

        parameter: {
            type: String,
            required: true
        },

        current_value: {
            type: mongoose.Schema.Types.Mixed
        },

        expected_value: {
            type: mongoose.Schema.Types.Mixed
        },

        anomaly_score: {
            type: Number,
            min: 0,
            max: 1
        },

        explanation: {
            type: String
        },

        context: {
            eclipse: Boolean,
            mission_mode: String,
            payload_active: Boolean,
            historical_deviation: String
        },

        acknowledgement: {
            type: String,
            enum: [
                "UNACKNOWLEDGED",
                "ACKNOWLEDGED",
                "RESOLVED"
            ],
            default: "UNACKNOWLEDGED"
        }
    },
    {
        timestamps: true,
        collection: "alerts"
    }
);

alertSchema.index({
    satellite_id: 1,
    timestamp: -1
});

alertSchema.index({
    severity: 1,
    timestamp: -1
});

module.exports = mongoose.model("Alert", alertSchema);