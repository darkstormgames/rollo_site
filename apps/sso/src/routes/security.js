const express = require('express');
const { body, param, query, validationResult } = require('express-validator');
const { SSHKey, TLSCertificate, User, sequelize } = require('../models');
const SSHKeyManager = require('../utils/ssh-key-manager');
const TLSCertificateManager = require('../utils/tls-certificate-manager');
const SecurityUtils = require('../utils/security');
const SecurityAuditLogger = require('../utils/security-audit-logger');
const authMiddleware = require('../middleware/auth').authenticateToken;

const router = express.Router();

// Get client IP helper
const getClientIP = (req) => {
    return req.ip || req.connection.remoteAddress || req.socket.remoteAddress ||
           (req.connection.socket ? req.connection.socket.remoteAddress : null);
};

// Generate SSH key pair
router.post('/keys/generate',
    authMiddleware,
    [
        body('name').isLength({ min: 1, max: 255 }).withMessage('Name is required'),
        body('description').optional().isLength({ max: 1000 }).withMessage('Description too long'),
        body('expiresInDays').optional().isInt({ min: 1, max: 3650 }).withMessage('Invalid expiration days')
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    error: 'Validation failed',
                    details: errors.array()
                });
            }

            const { name, description, expiresInDays } = req.body;
            const userId = req.user.id;
            const ipAddress = getClientIP(req);
            const userAgent = req.get('User-Agent');

            // Generate key pair
            const keyPair = SSHKeyManager.generateKeyPair();
            
            // Generate encryption key and encrypt private key
            const encryptionKey = SSHKeyManager.generateEncryptionKey();
            const encryptedPrivateKey = SSHKeyManager.encryptPrivateKey(
                keyPair.privateKey, 
                encryptionKey
            );

            // Calculate expiration date
            let expiresAt = null;
            if (expiresInDays) {
                expiresAt = new Date();
                expiresAt.setDate(expiresAt.getDate() + expiresInDays);
            }

            const transaction = await sequelize.transaction();
            try {
                // Store SSH key in database
                const sshKey = await SSHKey.create({
                    keyId: keyPair.keyId,
                    name,
                    description,
                    publicKey: keyPair.publicKey,
                    privateKeyEncrypted: encryptedPrivateKey.encrypted,
                    encryptionIv: encryptedPrivateKey.iv,
                    encryptionAuthTag: encryptedPrivateKey.authTag,
                    fingerprint: keyPair.fingerprint,
                    keySize: SSHKeyManager.KEY_SIZE,
                    expiresAt,
                    createdBy: userId
                }, { transaction });

                await transaction.commit();

                // Log audit event
                await SecurityAuditLogger.logSSHKeyGenerated(
                    keyPair.keyId,
                    userId,
                    ipAddress,
                    userAgent
                );

                res.status(201).json({
                    message: 'SSH key pair generated successfully',
                    key: {
                        keyId: sshKey.keyId,
                        name: sshKey.name,
                        publicKey: sshKey.publicKey,
                        fingerprint: sshKey.fingerprint,
                        keySize: sshKey.keySize,
                        expiresAt: sshKey.expiresAt,
                        createdAt: sshKey.createdAt
                    }
                });

            } catch (error) {
                await transaction.rollback();
                throw error;
            }

        } catch (error) {
            console.error('SSH key generation error:', error);
            res.status(500).json({
                error: 'Failed to generate SSH key',
                details: 'Internal server error'
            });
        }
    }
);

// List SSH keys
router.get('/keys',
    authMiddleware,
    [
        query('page').optional().isInt({ min: 1 }).withMessage('Invalid page number'),
        query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Invalid limit'),
        query('active').optional().isBoolean().withMessage('Active must be boolean')
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    error: 'Validation failed',
                    details: errors.array()
                });
            }

            const page = parseInt(req.query.page) || 1;
            const limit = parseInt(req.query.limit) || 20;
            const active = req.query.active !== undefined ? req.query.active === 'true' : null;
            const offset = (page - 1) * limit;

            const where = { createdBy: req.user.id };
            if (active !== null) {
                where.isActive = active;
            }

            const result = await SSHKey.findAndCountAll({
                where,
                attributes: [
                    'id', 'keyId', 'name', 'description', 'fingerprint',
                    'keySize', 'isActive', 'lastUsed', 'expiresAt',
                    'createdAt', 'revokedAt', 'revocationReason'
                ],
                order: [['createdAt', 'DESC']],
                limit,
                offset
            });

            res.json({
                keys: result.rows,
                pagination: {
                    page,
                    limit,
                    total: result.count,
                    pages: Math.ceil(result.count / limit)
                }
            });

        } catch (error) {
            console.error('List SSH keys error:', error);
            res.status(500).json({
                error: 'Failed to list SSH keys',
                details: 'Internal server error'
            });
        }
    }
);

// Deploy SSH key to server
router.post('/keys/:keyId/deploy',
    authMiddleware,
    [
        param('keyId').isUUID().withMessage('Invalid key ID'),
        body('host').isIP().withMessage('Invalid host IP address'),
        body('port').optional().isInt({ min: 1, max: 65535 }).withMessage('Invalid port'),
        body('username').isLength({ min: 1, max: 255 }).withMessage('Username is required'),
        body('password').optional().isLength({ min: 1 }).withMessage('Password cannot be empty'),
        body('existingKeyId').optional().isUUID().withMessage('Invalid existing key ID')
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    error: 'Validation failed',
                    details: errors.array()
                });
            }

            const { keyId } = req.params;
            const { host, port = 22, username, password, existingKeyId } = req.body;
            const userId = req.user.id;
            const ipAddress = getClientIP(req);
            const userAgent = req.get('User-Agent');

            // Find SSH key
            const sshKey = await SSHKey.findOne({
                where: {
                    keyId,
                    createdBy: userId,
                    isActive: true
                }
            });

            if (!sshKey) {
                return res.status(404).json({
                    error: 'SSH key not found or not accessible'
                });
            }

            // Check if key is expired
            if (sshKey.expiresAt && new Date() > sshKey.expiresAt) {
                return res.status(400).json({
                    error: 'SSH key has expired'
                });
            }

            // Prepare connection config
            const hostConfig = {
                host,
                port,
                username,
                password
            };

            // If using existing key for authentication, decrypt it
            if (existingKeyId && !password) {
                const existingKey = await SSHKey.findOne({
                    where: {
                        keyId: existingKeyId,
                        createdBy: userId,
                        isActive: true
                    }
                });

                if (!existingKey) {
                    return res.status(404).json({
                        error: 'Existing authentication key not found'
                    });
                }

                // For demo purposes, we'll skip actual decryption
                // In production, you'd need to decrypt the private key
                hostConfig.privateKey = 'decrypted-private-key-content';
            }

            // Deploy key
            const deployResult = await SSHKeyManager.deployKey(hostConfig, sshKey.publicKey);
            
            // Update last used timestamp
            await sshKey.update({ lastUsed: new Date() });

            // Log audit event
            await SecurityAuditLogger.logSSHKeyDeployed(
                keyId,
                host,
                userId,
                ipAddress,
                userAgent,
                true
            );

            res.json({
                message: 'SSH key deployed successfully',
                result: deployResult
            });

        } catch (error) {
            console.error('SSH key deployment error:', error);
            
            // Log failure
            await SecurityAuditLogger.logSSHKeyDeployed(
                req.params.keyId,
                req.body.host,
                req.user.id,
                getClientIP(req),
                req.get('User-Agent'),
                false
            );

            res.status(500).json({
                error: 'Failed to deploy SSH key',
                details: error.message
            });
        }
    }
);

// Revoke SSH key
router.delete('/keys/:keyId',
    authMiddleware,
    [
        param('keyId').isUUID().withMessage('Invalid key ID'),
        body('reason').optional().isLength({ max: 255 }).withMessage('Reason too long')
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    error: 'Validation failed',
                    details: errors.array()
                });
            }

            const { keyId } = req.params;
            const { reason } = req.body;
            const userId = req.user.id;
            const ipAddress = getClientIP(req);
            const userAgent = req.get('User-Agent');

            const sshKey = await SSHKey.findOne({
                where: {
                    keyId,
                    createdBy: userId,
                    isActive: true
                }
            });

            if (!sshKey) {
                return res.status(404).json({
                    error: 'SSH key not found or already revoked'
                });
            }

            // Revoke key
            await sshKey.update({
                isActive: false,
                revokedAt: new Date(),
                revokedBy: userId,
                revocationReason: reason || 'Manual revocation'
            });

            // Log audit event
            await SecurityAuditLogger.logSSHKeyRevoked(
                keyId,
                reason || 'Manual revocation',
                userId,
                ipAddress,
                userAgent
            );

            res.json({
                message: 'SSH key revoked successfully'
            });

        } catch (error) {
            console.error('SSH key revocation error:', error);
            res.status(500).json({
                error: 'Failed to revoke SSH key',
                details: 'Internal server error'
            });
        }
    }
);

// Generate TLS certificate
router.post('/certs/generate',
    authMiddleware,
    [
        body('name').isLength({ min: 1, max: 255 }).withMessage('Name is required'),
        body('commonName').isLength({ min: 1, max: 255 }).withMessage('Common name is required'),
        body('organization').optional().isLength({ max: 255 }).withMessage('Organization name too long'),
        body('validityDays').optional().isInt({ min: 1, max: 3650 }).withMessage('Invalid validity days'),
        body('altNames').optional().isArray().withMessage('Alt names must be an array')
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    error: 'Validation failed',
                    details: errors.array()
                });
            }

            const { name, commonName, organization, validityDays, altNames } = req.body;
            const userId = req.user.id;
            const ipAddress = getClientIP(req);
            const userAgent = req.get('User-Agent');

            // Generate certificate
            const certData = TLSCertificateManager.generateCertificate({
                commonName,
                organization,
                validityDays,
                altNames
            });

            // Encrypt private key
            const encryptionPassword = SecurityUtils.generateSecureRandom(32);
            const encryptedPrivateKey = TLSCertificateManager.encryptPrivateKey(
                certData.privateKey,
                encryptionPassword
            );

            const transaction = await sequelize.transaction();
            try {
                // Store certificate in database
                const tlsCert = await TLSCertificate.create({
                    certificateId: certData.certificateId,
                    name,
                    certificate: certData.certificate,
                    privateKeyEncrypted: encryptedPrivateKey,
                    publicKey: certData.publicKey,
                    fingerprint: certData.fingerprint,
                    serialNumber: certData.serialNumber,
                    subject: certData.subject,
                    issuer: certData.subject, // Self-signed
                    validFrom: certData.validFrom,
                    validTo: certData.validTo,
                    createdBy: userId
                }, { transaction });

                await transaction.commit();

                // Log audit event
                await SecurityAuditLogger.logTLSCertGenerated(
                    certData.certificateId,
                    commonName,
                    userId,
                    ipAddress,
                    userAgent
                );

                res.status(201).json({
                    message: 'TLS certificate generated successfully',
                    certificate: {
                        certificateId: tlsCert.certificateId,
                        name: tlsCert.name,
                        certificate: tlsCert.certificate,
                        fingerprint: tlsCert.fingerprint,
                        subject: tlsCert.subject,
                        validFrom: tlsCert.validFrom,
                        validTo: tlsCert.validTo,
                        createdAt: tlsCert.createdAt
                    }
                });

            } catch (error) {
                await transaction.rollback();
                throw error;
            }

        } catch (error) {
            console.error('TLS certificate generation error:', error);
            res.status(500).json({
                error: 'Failed to generate TLS certificate',
                details: 'Internal server error'
            });
        }
    }
);

// List TLS certificates
router.get('/certs',
    authMiddleware,
    [
        query('page').optional().isInt({ min: 1 }).withMessage('Invalid page number'),
        query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Invalid limit'),
        query('active').optional().isBoolean().withMessage('Active must be boolean')
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    error: 'Validation failed',
                    details: errors.array()
                });
            }

            const page = parseInt(req.query.page) || 1;
            const limit = parseInt(req.query.limit) || 20;
            const active = req.query.active !== undefined ? req.query.active === 'true' : null;
            const offset = (page - 1) * limit;

            const where = { createdBy: req.user.id };
            if (active !== null) {
                where.isActive = active;
            }

            const result = await TLSCertificate.findAndCountAll({
                where,
                attributes: [
                    'id', 'certificateId', 'name', 'fingerprint',
                    'subject', 'validFrom', 'validTo', 'isActive',
                    'lastUsed', 'createdAt', 'revokedAt'
                ],
                order: [['createdAt', 'DESC']],
                limit,
                offset
            });

            res.json({
                certificates: result.rows,
                pagination: {
                    page,
                    limit,
                    total: result.count,
                    pages: Math.ceil(result.count / limit)
                }
            });

        } catch (error) {
            console.error('List TLS certificates error:', error);
            res.status(500).json({
                error: 'Failed to list TLS certificates',
                details: 'Internal server error'
            });
        }
    }
);

module.exports = router;