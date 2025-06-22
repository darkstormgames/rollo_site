const JWTManager = require('../utils/jwt-manager');
const SecurityUtils = require('../utils/security');
const { User, RefreshToken } = require('../models');

const authenticateToken = async (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ 
            error: 'Access token required',
            code: 'TOKEN_MISSING'
        });
    }

    try {
        const decoded = await JWTManager.verifyAccessToken(token);
        // Verify user still exists and is active
        const user = await User.findOne({
            where: {
                id: decoded.userId,
                is_active: true
            },
            attributes: ['id', 'username', 'email', 'access_level', 'is_active']
        });
        if (!user) {
            return res.status(401).json({ 
                error: 'User not found or inactive',
                code: 'USER_INACTIVE'
            });
        }

        req.user = {
            id: user.id,
            username: user.username,
            email: user.email,
            access_level: user.access_level
        };
        req.tokenData = decoded;
        next();
    } catch (error) {
        console.error('Token verification error:', error);
        return res.status(403).json({ 
            error: 'Invalid or expired token',
            code: 'TOKEN_INVALID'
        });
    }
};

const authenticateRefreshToken = async (req, res, next) => {
    const { refreshToken } = req.body;

    if (!refreshToken) {
        return res.status(401).json({ 
            error: 'Refresh token required',
            code: 'REFRESH_TOKEN_MISSING'
        });
    }

    try {
        const decoded = await JWTManager.verifyRefreshToken(refreshToken);
        
        // Check if refresh token exists and is not revoked
        const tokenHash = SecurityUtils.hashSensitiveData(refreshToken);
        const tokenRecord = await RefreshToken.findOne({
            where: {
                user_id: decoded.userId,
                token_hash: tokenHash,
                revoked_at: null
            },
            include: [{
                model: User,
                as: 'user',
                attributes: ['id', 'username', 'email', 'access_level', 'is_active']
            }]
        });

        if (!tokenRecord || new Date() > tokenRecord.expires_at) {
            return res.status(403).json({ 
                error: 'Invalid or expired refresh token',
                code: 'REFRESH_TOKEN_INVALID'
            });
        }

        if (!tokenRecord.user.is_active) {
            return res.status(401).json({ 
                error: 'User account is inactive',
                code: 'USER_INACTIVE'
            });
        }

        req.user = {
            id: tokenRecord.user.id,
            username: tokenRecord.user.username,
            email: tokenRecord.user.email,
            access_level: tokenRecord.user.access_level
        };
        req.refreshTokenData = decoded;
        next();
    } catch (error) {
        return res.status(403).json({ 
            error: 'Invalid refresh token',
            code: 'REFRESH_TOKEN_INVALID'
        });
    }
};

const optionalAuth = async (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return next();
    }

    try {
        const decoded = await JWTManager.verifyAccessToken(token);
        const user = await User.findOne({
            where: {
                id: decoded.userId,
                is_active: true
            },
            attributes: ['id', 'username', 'email', 'access_level']
        });

        if (user) {
            req.user = {
                id: user.id,
                username: user.username,
                email: user.email,
                access_level: user.access_level
            };
            req.tokenData = decoded;
        }
    } catch (error) {
        // Ignore token errors for optional auth
    }

    next();
};

module.exports = {
    authenticateToken,
    authenticateRefreshToken,
    optionalAuth
};