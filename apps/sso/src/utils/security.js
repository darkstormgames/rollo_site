const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

class SecurityUtils {
    static SALT_ROUNDS = 12;

    /**
     * Hash password securely using bcrypt
     */
    static async hashPassword(password) {
        return bcrypt.hash(password, this.SALT_ROUNDS);
    }

    /**
     * Verify password against hash
     */
    static async verifyPassword(password, hash) {
        return bcrypt.compare(password, hash);
    }

    /**
     * Generate secure random string
     */
    static generateSecureRandom(length = 32) {
        return crypto.randomBytes(length).toString('hex');
    }

    /**
     * Generate JWT token with configurable expiration
     */
    static generateToken(payload, secret, expiresIn = '15m') {
        return jwt.sign(payload, secret, { 
            expiresIn,
            issuer: 'rollo-sso',
            audience: 'rollo-sites'
        });
    }

    /**
     * Verify and decode JWT token
     */
    static verifyToken(token, secret) {
        try {
            return jwt.verify(token, secret, {
                issuer: 'rollo-sso',
                audience: 'rollo-sites'
            });
        } catch (error) {
            throw new Error('Invalid or expired token');
        }
    }

    /**
     * Generate UUID for key rotation
     */
    static generateKeyId() {
        return uuidv4();
    }

    /**
     * Hash sensitive data for storage
     */
    static hashSensitiveData(data) {
        return crypto.createHash('sha256').update(data).digest('hex');
    }

    /**
     * Generate secure API key
     */
    static generateApiKey() {
        return crypto.randomBytes(32).toString('base64');
    }

    /**
     * Constant time string comparison to prevent timing attacks
     */
    static constantTimeCompare(a, b) {
        if (a.length !== b.length) {
            return false;
        }
        
        let result = 0;
        for (let i = 0; i < a.length; i++) {
            result |= a.charCodeAt(i) ^ b.charCodeAt(i);
        }
        return result === 0;
    }
}

module.exports = SecurityUtils;