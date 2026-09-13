require("dotenv").config();

const express = require("express");
const cors = require("cors");

const connectDatabase = require("./config/database");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
    res.json({
        project: "ORBIT-X",
        status: "online"
    });
});

const PORT = process.env.PORT || 5000;

const startServer = async () => {
    await connectDatabase();

    app.listen(PORT, () => {
        console.log(`ORBIT-X backend running on port ${PORT}`);
    });
};

startServer();