const mongoose = require("mongoose");

const communicationEventSchema = new mongoose.Schema(
    {
        satellite_id: {
            type: Number,
            required: true,
            index: true
        },

        ground_station_id: {
            type: String,
            required: true,
            index: true
        },

        start_time: {
            type: Date,
            required: true
        },

        end_time: {
            type: Date,
            required: true
        },

        signal_strength_dbm: {
            type: Number
        },

        packets_received: {
            type: Number,
            default: 0
        },

        packets_lost: {
            type: Number,
            default: 0
        },

        status: {
            type: String,
            enum: [
                "SUCCESS",
                "PARTIAL",
                "FAILED"
            ],
            default: "SUCCESS"
        }
    },
    {
        timestamps: true,
        collection: "communication_events"
    }
);

communicationEventSchema.index({
    satellite_id: 1,
    start_time: -1
});

communicationEventSchema.index({
    ground_station_id: 1,
    start_time: -1
});

module.exports = mongoose.model(
    "CommunicationEvent",
    communicationEventSchema
);