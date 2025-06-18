const db = require('../config/database');
const SecurityUtils = require('../utils/security');

class JWTManager {
    static ACCESS_TOKEN_TYPE = 'access';
    static REFRESH_TOKEN_TYPE = 'refresh';

    /**
     * Initialize JWT secrets on server startup
     */
    static async initializeSecrets() {
        try {
            // Check if we have active secrets
            const existingSecrets = await db.query(
                'SELECT * FROM jwt_secrets WHERE is_active = TRUE'
            );

            if (existingSecrets.length === 0) {
                // Generate initial secrets
                await this.rotateSecrets();
            }
        } catch (error) {
            console.error('Failed to initialize JWT secrets:', error);
            throw error;
        }
    }

    /**
     * Rotate JWT secrets for enhanced security
     */
    static async rotateSecrets() {
        const accessKeyId = SecurityUtils.generateKeyId();
        const refreshKeyId = SecurityUtils.generateKeyId();
        
        const accessSecret = SecurityUtils.generateSecureRandom(64);
        const refreshSecret = SecurityUtils.generateSecureRandom(64);

        const accessSecretHash = SecurityUtils.hashSensitiveData(accessSecret);
        const refreshSecretHash = SecurityUtils.hashSensitiveData(refreshSecret);

        await db.transaction(async (connection) => {
            // Deactivate old secrets
            await connection.execute(
                'UPDATE jwt_secrets SET is_active = FALSE WHERE is_active = TRUE'
            );

            // Insert new secrets
            await connection.execute(`
                INSERT INTO jwt_secrets (key_id, secret_hash, type, is_active) 
                VALUES (?, ?, ?, TRUE), (?, ?, ?, TRUE)
            `, [
                accessKeyId, accessSecretHash, this.ACCESS_TOKEN_TYPE,
                refreshKeyId, refreshSecretHash, this.REFRESH_TOKEN_TYPE
            ]);
        });

        // Store in memory for immediate use (in production, use secure key management)
        this.currentSecrets = {
            access: { keyId: accessKeyId, secret: accessSecret },
            refresh: { keyId: refreshKeyId, secret: refreshSecret }
        };

        console.log('JWT secrets rotated successfully');
    }

    /**
     * Get current active secret by type
     */
    static async getActiveSecret(type) {
        if (!this.currentSecrets || !this.currentSecrets[type]) {
            await this.loadActiveSecrets();
        }
        return this.currentSecrets[type];
    }

    /**
     * Load active secrets from database
     */
    static async loadActiveSecrets() {
        const secrets = await db.query(
            'SELECT key_id, type FROM jwt_secrets WHERE is_active = TRUE'
        );

        this.currentSecrets = {};
        for (const secret of secrets) {
            // In production, retrieve actual secret from secure vault
            // For now, we'll regenerate (this is a limitation for demo)
            this.currentSecrets[secret.type] = {
                keyId: secret.key_id,
                secret: process.env[`JWT_${secret.type.toUpperCase()}_SECRET`] || SecurityUtils.generateSecureRandom(64)
            };
        }
    }

    /**
     * Generate access token
     */
    static async generateAccessToken(payload) {
        const secret = await this.getActiveSecret(this.ACCESS_TOKEN_TYPE);
        return SecurityUtils.generateToken(
            { ...payload, keyId: secret.keyId },
            secret.secret,
            process.env.JWT_ACCESS_EXPIRES_IN || '15m'
        );
    }

    /**
     * Generate refresh token
     */
    static async generateRefreshToken(payload) {
        const secret = await this.getActiveSecret(this.REFRESH_TOKEN_TYPE);
        return SecurityUtils.generateToken(
            { ...payload, keyId: secret.keyId },
            secret.secret,
            process.env.JWT_REFRESH_EXPIRES_IN || '7d'
        );
    }

    /**
     * Verify access token
     */
    static async verifyAccessToken(token) {
        const secret = await this.getActiveSecret(this.ACCESS_TOKEN_TYPE);
        return SecurityUtils.verifyToken(token, secret.secret);
    }

    /**
     * Verify refresh token
     */
    static async verifyRefreshToken(token) {
        const secret = await this.getActiveSecret(this.REFRESH_TOKEN_TYPE);
        return SecurityUtils.verifyToken(token, secret.secret);
    }
}

module.exports = JWTManager;