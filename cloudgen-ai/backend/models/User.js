const mongoose = require("mongoose");

const userSchema = new mongoose.Schema({
  name: String,
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  awsCredentials: {
    accessKeyId: { type: String },
    secretAccessKey: { type: String },
  },
});

module.exports = mongoose.model("User", userSchema);
