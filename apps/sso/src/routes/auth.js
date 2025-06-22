const express = require('express');
const { body, validationResult } = require('express-validator');
const { User, RefreshToken, UserSession } = require('../models');
const SecurityUtils = require('../utils/security');
const JWTManager = require('../utils/jwt-manager');
const AccessLevelService = require('../services/AccessLevelService');
const { authenticateRefreshToken, authenticateToken } = require('../middleware/auth');

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
        const existingUser = await User.findOne({
            where: {
                [require('sequelize').Op.or]: [
                    { username },
                    { email }
                ]
            }
        });

        if (existingUser) {
            return res.status(409).json({
                error: 'User already exists with this username or email'
            });
        }

        // Hash password securely
        const passwordHash = await SecurityUtils.hashPassword(password);

        // Create user
        const user = await User.create({
            username,
            email,
            password_hash: passwordHash,
            first_name: firstName || null,
            last_name: lastName || null,
            access_level: 'basic' // Default access level
        });

        res.status(201).json({
            message: 'User registered successfully',
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                firstName: user.first_name,
                lastName: user.last_name,
                accessLevel: user.access_level
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
        const user = await User.findOne({
            where: {
                [require('sequelize').Op.and]: [
                    {
                        [require('sequelize').Op.or]: [
                            { username },
                            { email: username }
                        ]
                    },
                    { is_active: true }
                ]
            }
        });

        if (!user) {
            return res.status(401).json({
                error: 'Invalid credentials'
            });
        }

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
            email: user.email,
            accessLevel: user.access_level
        };

        const accessToken = await JWTManager.generateAccessToken(tokenPayload);
        const refreshToken = await JWTManager.generateRefreshToken(tokenPayload);

        // Store refresh token in database
        const refreshTokenHash = SecurityUtils.hashSensitiveData(refreshToken);
        const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

        await RefreshToken.create({
            user_id: user.id,
            token_hash: refreshTokenHash,
            expires_at: expiresAt
        });

        // Create session record
        const sessionId = SecurityUtils.generateSecureRandom(32);
        const sessionExpiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

        await UserSession.create({
            user_id: user.id,
            session_id: sessionId,
            ip_address: req.ip || req.connection.remoteAddress,
            user_agent: req.get('User-Agent') || '',
            expires_at: sessionExpiresAt
        });

        // Get accessible sites
        const accessibleSites = await AccessLevelService.getAccessibleSites(user.id);

        res.json({
            message: 'Login successful',
            accessToken,
            refreshToken,
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                firstName: user.first_name,
                lastName: user.last_name,
                accessLevel: user.access_level
            },
            accessibleSites: accessibleSites.map(site => ({
                id: site.id,
                name: site.site_name,
                url: site.site_url,
                requiredAccessLevel: site.access_level_required
            }))
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
            const refreshTokenHash = SecurityUtils.hashSensitiveData(refreshToken);
            await RefreshToken.update(
                { revoked_at: new Date() },
                { 
                    where: { 
                        token_hash: refreshTokenHash,
                        revoked_at: null 
                    } 
                }
            );
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

// Get user's accessible sites
router.get('/sites', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.id;
        const accessibleSites = await AccessLevelService.getAccessibleSites(userId);

        res.json({
            sites: accessibleSites.map(site => ({
                id: site.id,
                name: site.site_name,
                url: site.site_url,
                requiredAccessLevel: site.access_level_required
            }))
        });

    } catch (error) {
        console.error('Get sites error:', error);
        res.status(500).json({
            error: 'Failed to get accessible sites',
            details: 'Internal server error'
        });
    }
});

// Admin routes for access level management
router.put('/admin/users/:userId/access-level', authenticateToken, async (req, res) => {
    try {
        const adminUserId = req.user.id;
        const { userId } = req.params;
        const { accessLevel } = req.body;

        const updatedUser = await AccessLevelService.updateUserAccessLevel(
            adminUserId, 
            userId, 
            accessLevel
        );

        res.json({
            message: 'User access level updated successfully',
            user: {
                id: updatedUser.id,
                username: updatedUser.username,
                email: updatedUser.email,
                accessLevel: updatedUser.access_level
            }
        });

    } catch (error) {
        console.error('Update user access level error:', error);
        res.status(error.message.includes('Insufficient permissions') ? 403 : 500).json({
            error: error.message,
            details: error.message.includes('Insufficient permissions') ? 'Admin access required' : 'Internal server error'
        });
    }
});

router.put('/admin/sites/:siteId/access-level', authenticateToken, async (req, res) => {
    try {
        const adminUserId = req.user.id;
        const { siteId } = req.params;
        const { requiredAccessLevel } = req.body;

        const updatedSite = await AccessLevelService.updateSiteAccessLevel(
            adminUserId, 
            siteId, 
            requiredAccessLevel
        );

        res.json({
            message: 'Site access level updated successfully',
            site: {
                id: updatedSite.id,
                name: updatedSite.site_name,
                url: updatedSite.site_url,
                requiredAccessLevel: updatedSite.access_level_required
            }
        });

    } catch (error) {
        console.error('Update site access level error:', error);
        res.status(error.message.includes('Insufficient permissions') ? 403 : 500).json({
            error: error.message,
            details: error.message.includes('Insufficient permissions') ? 'Admin access required' : 'Internal server error'
        });
    }
});

router.get('/admin/users', authenticateToken, async (req, res) => {
    try {
        const adminUserId = req.user.id;
        const { accessLevel } = req.query;

        const users = await AccessLevelService.getUsersByAccessLevel(adminUserId, accessLevel);

        res.json({
            users: users.map(user => ({
                id: user.id,
                username: user.username,
                email: user.email,
                firstName: user.first_name,
                lastName: user.last_name,
                accessLevel: user.access_level,
                createdAt: user.created_at
            }))
        });

    } catch (error) {
        console.error('Get users error:', error);
        res.status(error.message.includes('Insufficient permissions') ? 403 : 500).json({
            error: error.message,
            details: error.message.includes('Insufficient permissions') ? 'Admin access required' : 'Internal server error'
        });
    }
});

router.get('/me', authenticateToken, async (req, res) => {
    try {
        if (!req.user) {
            return res.status(404).json({ error: 'User not found' });
        }

        const user = req.user;
        const accessibleSites = await AccessLevelService.getAccessibleSites(user.id);

        console.log(`Accessible sites for user ${user.id}:`, accessibleSites);
        console.log(`User details:`, {
            id: user.id,
            username: user.username,
            email: user.email,
            firstName: user.first_name,
            lastName: user.last_name,
            accessLevel: user.access_level,
            createdAt: user.created_at,
            isActive: user.is_active
        });

        res.json({
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                firstName: user.first_name,
                lastName: user.last_name,
                accessLevel: user.access_level,
                createdAt: user.created_at,
                isActive: user.is_active
            },
            accessibleSites: accessibleSites.map(site => ({
                id: site.id,
                name: site.site_name,
                url: site.site_url,
                requiredAccessLevel: site.access_level_required
            }))
        });
    } catch (error) {
        console.error('User /me error:', error);
        res.status(401).json({ error: 'Invalid or expired token' });
    }
});

module.exports = router;