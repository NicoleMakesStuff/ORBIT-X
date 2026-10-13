const path = require("path");

require("dotenv").config({
    path: path.resolve(__dirname, "../../.env")
});

const connectDatabase = require("./config/database");
const app = require("./app");

const PORT = process.env.PORT || 5000;

const startServer = async () => {
    await connectDatabase();

    app.listen(PORT, () => {
        console.log(`ORBIT-X backend running on port ${PORT}`);
    });
};

startServer();