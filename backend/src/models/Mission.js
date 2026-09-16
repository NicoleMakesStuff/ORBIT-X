const mongoose = require("mongoose");

const missionSchema = new mongoose.Schema(
    {
        mission_id: {
            type: String,
            required: true,
            unique: true,
            index: true
        },

        name: {
            type: String,
            required: true
        },

        description: {
            type: String
        },

        mission_type: {
            type: String
        },

        operator: {
            type: String
        },

        status: {
            type: String,
            enum: [
                "PLANNED",
                "ACTIVE",
                "COMPLETED",
                "FAILED",
                "DECOMMISSIONED"
            ],
            default: "PLANNED"
        },

        start_date: {
            type: Date
        },

        end_date: {
            type: Date
        }
    },
    {
        timestamps: true,
        collection: "missions"
    }
);

module.exports = mongoose.model("Mission", missionSchema);