const { JwtSecret, sequelize } = require('../models');
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
            const existingSecrets = await JwtSecret.findAll({
                where: { is_active: true }
            });

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

        const transaction = await sequelize.transaction();
        try {
            // Deactivate old secrets
            await JwtSecret.update(
                { is_active: false },
                { 
                    where: { is_active: true },
                    transaction
                }
            );

            // Insert new secrets
            await JwtSecret.bulkCreate([
                {
                    key_id: accessKeyId,
                    secret_hash: accessSecretHash,
                    type: this.ACCESS_TOKEN_TYPE,
                    is_active: true
                },
                {
                    key_id: refreshKeyId,
                    secret_hash: refreshSecretHash,
                    type: this.REFRESH_TOKEN_TYPE,
                    is_active: true
                }
            ], { transaction });

            await transaction.commit();
        } catch (error) {
            await transaction.rollback();
            throw error;
        }

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
        const secrets = await JwtSecret.findAll({
            where: { is_active: true },
            attributes: ['key_id', 'type']
        });

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