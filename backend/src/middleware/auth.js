const JWTManager = require('../utils/jwt-manager');
const db = require('../config/database');

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
        const user = await db.query(
            'SELECT id, username, email, is_active FROM users WHERE id = ? AND is_active = TRUE',
            [decoded.userId]
        );

        if (user.length === 0) {
            return res.status(401).json({ 
                error: 'User not found or inactive',
                code: 'USER_INACTIVE'
            });
        }

        req.user = user[0];
        req.tokenData = decoded;
        next();
    } catch (error) {
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
        const tokenRecord = await db.query(`
            SELECT rt.*, u.username, u.email, u.is_active 
            FROM refresh_tokens rt 
            JOIN users u ON rt.user_id = u.id
            WHERE rt.user_id = ? AND rt.token_hash = SHA2(?, 256) 
            AND rt.expires_at > NOW() AND rt.revoked_at IS NULL
        `, [decoded.userId, refreshToken]);

        if (tokenRecord.length === 0) {
            return res.status(403).json({ 
                error: 'Invalid or expired refresh token',
                code: 'REFRESH_TOKEN_INVALID'
            });
        }

        if (!tokenRecord[0].is_active) {
            return res.status(401).json({ 
                error: 'User account is inactive',
                code: 'USER_INACTIVE'
            });
        }

        req.user = {
            id: tokenRecord[0].user_id,
            username: tokenRecord[0].username,
            email: tokenRecord[0].email
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
        const user = await db.query(
            'SELECT id, username, email FROM users WHERE id = ? AND is_active = TRUE',
            [decoded.userId]
        );

        if (user.length > 0) {
            req.user = user[0];
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