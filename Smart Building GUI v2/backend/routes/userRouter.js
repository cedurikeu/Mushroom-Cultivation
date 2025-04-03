import express from "express";

import { registerUser, loginUser } from "../controller/userController.js";

const router = express.Router();

// User registration
router.post("/register", registerUser);

// User login
router.post("/login", loginUser);

export default router;
