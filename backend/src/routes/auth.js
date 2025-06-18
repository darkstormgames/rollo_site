const express = require('express');
const { body, validationResult } = require('express-validator');
const db = require('../config/database');
const SecurityUtils = require('../utils/security');
const JWTManager = require('../utils/jwt-manager');
const { authenticateRefreshToken } = require('../middleware/auth');

const router = express.Router();

// Validation rules
const registerValidation = [
    body('username')
        .isLength({ min: 3, max: 50 })
        .matches(/^[a-zA-Z0-9_]+$/)
        .withMessage('Username must be 3-50 characters and contain only letters, numbers, and underscores'),
    body('email')
        .isEmail()
        .normalizeEmail()
        .withMessage('Valid email is required'),
    body('password')
        .isLength({ min: 8 })
        .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
        .withMessage('Password must be at least 8 characters with uppercase, lowercase, number, and special character'),
    body('firstName')
        .optional()
        .isLength({ max: 50 })
        .trim(),
    body('lastName')
        .optional()
        .isLength({ max: 50 })
        .trim()
];

const loginValidation = [
    body('username')
        .notEmpty()
        .withMessage('Username or email is required'),
    body('password')
        .notEmpty()
        .withMessage('Password is required')
];

// Register new user
router.post('/register', registerValidation, async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const { username, email, password, firstName, lastName } = req.body;

        // Check if user already exists
        const existingUser = await db.query(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            [username, email]
        );

        if (existingUser.length > 0) {
            return res.status(409).json({
                error: 'User already exists with this username or email'
            });
        }

        // Hash password securely
        const passwordHash = await SecurityUtils.hashPassword(password);

        // Create user
        const result = await db.query(`
            INSERT INTO users (username, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        `, [username, email, passwordHash, firstName || null, lastName || null]);

        const userId = result.insertId;

        res.status(201).json({
            message: 'User registered successfully',
            user: {
                id: userId,
                username,
                email,
                firstName: firstName || null,
                lastName: lastName || null
            }
        });

    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({
            error: 'Registration failed',
            details: 'Internal server error'
        });
    }
});

// Login user
router.post('/login', loginValidation, async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                error: 'Validation failed',
                details: errors.array()
            });
        }

        const { username, password } = req.body;

        // Find user by username or email
        const users = await db.query(
            'SELECT id, username, email, password_hash, first_name, last_name, is_active FROM users WHERE (username = ? OR email = ?) AND is_active = TRUE',
            [username, username]
        );

        if (users.length === 0) {
            return res.status(401).json({
                error: 'Invalid credentials'
            });
        }

        const user = users[0];

        // Verify password
        const isValidPassword = await SecurityUtils.verifyPassword(password, user.password_hash);
        if (!isValidPassword) {
            return res.status(401).json({
                error: 'Invalid credentials'
            });
        }

        // Generate tokens
        const tokenPayload = {
            userId: user.id,
            username: user.username,
            email: user.email
        };

        const accessToken = await JWTManager.generateAccessToken(tokenPayload);
        const refreshToken = await JWTManager.generateRefreshToken(tokenPayload);

        // Store refresh token in database
        const refreshTokenHash = SecurityUtils.hashSensitiveData(refreshToken);
        const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

        await db.query(`
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
        `, [user.id, refreshTokenHash, expiresAt]);

        // Create session record
        const sessionId = SecurityUtils.generateSecureRandom(32);
        const sessionExpiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

        await db.query(`
            INSERT INTO user_sessions (user_id, session_id, ip_address, user_agent, expires_at)
            VALUES (?, ?, ?, ?, ?)
        `, [
            user.id,
            sessionId,
            req.ip || req.connection.remoteAddress,
            req.get('User-Agent') || '',
            sessionExpiresAt
        ]);

        res.json({
            message: 'Login successful',
            accessToken,
            refreshToken,
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                firstName: user.first_name,
                lastName: user.last_name
            }
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({
            error: 'Login failed',
            details: 'Internal server error'
        });
    }
});

// Refresh token
router.post('/refresh', authenticateRefreshToken, async (req, res) => {
    try {
        const { refreshToken } = req.body;
        const user = req.user;

        // Generate new access token
        const tokenPayload = {
            userId: user.id,
            username: user.username,
            email: user.email
        };

        const newAccessToken = await JWTManager.generateAccessToken(tokenPayload);

        res.json({
            message: 'Token refreshed successfully',
            accessToken: newAccessToken
        });

    } catch (error) {
        console.error('Token refresh error:', error);
        res.status(500).json({
            error: 'Token refresh failed',
            details: 'Internal server error'
        });
    }
});

// Logout user
router.post('/logout', async (req, res) => {
    try {
        const { refreshToken } = req.body;

        if (refreshToken) {
            // Revoke refresh token
            await db.query(`
                UPDATE refresh_tokens 
                SET revoked_at = NOW() 
                WHERE token_hash = SHA2(?, 256) AND revoked_at IS NULL
            `, [refreshToken]);
        }

        res.json({
            message: 'Logout successful'
        });

    } catch (error) {
        console.error('Logout error:', error);
        res.status(500).json({
            error: 'Logout failed',
            details: 'Internal server error'
        });
    }
});

module.exports = router;