const cron = require('node-cron');
const { SSHKey, TLSCertificate, User, sequelize } = require('../models');
const SSHKeyManager = require('./ssh-key-manager');
const TLSCertificateManager = require('./tls-certificate-manager');
const SecurityAuditLogger = require('./security-audit-logger');
const { Op } = require('sequelize');

class KeyRotationManager {
    static isScheduled = false;

    /**
     * Initialize key rotation scheduler
     */
    static initializeScheduler() {
        if (this.isScheduled) {
            return;
        }

        // Run daily at 2 AM
        cron.schedule('0 2 * * *', () => {
            this.performScheduledRotation();
        });

        // Run weekly certificate check on Sundays at 3 AM
        cron.schedule('0 3 * * 0', () => {
            this.performCertificateRenewal();
        });

        this.isScheduled = true;
        console.log('✅ Key rotation scheduler initialized');
    }

    /**
     * Perform scheduled SSH key rotation
     */
    static async performScheduledRotation() {
        console.log('🔄 Starting scheduled SSH key rotation...');
        
        try {
            // Find SSH keys that need rotation (90 days old)
            const rotationDate = new Date();
            rotationDate.setDate(rotationDate.getDate() - 90);

            const keysNeedingRotation = await SSHKey.findAll({
                where: {
                    isActive: true,
                    createdAt: {
                        [Op.lte]: rotationDate
                    },
                    revokedAt: null
                },
                include: [{
                    model: User,
                    as: 'creator',
                    attributes: ['id', 'username', 'email']
                }]
            });

            console.log(`Found ${keysNeedingRotation.length} SSH keys requiring rotation`);

            for (const key of keysNeedingRotation) {
                await this.rotateSSHKey(key);
            }

            console.log('✅ Scheduled SSH key rotation completed');
        } catch (error) {
            console.error('❌ Scheduled SSH key rotation failed:', error);
            
            await SecurityAuditLogger.logEvent({
                eventType: SecurityAuditLogger.EVENT_TYPES.SSH_KEY_ROTATED,
                resourceType: SecurityAuditLogger.RESOURCE_TYPES.SSH_KEY,
                action: 'Scheduled SSH key rotation',
                result: SecurityAuditLogger.RESULTS.ERROR,
                errorMessage: error.message,
                severity: SecurityAuditLogger.SEVERITIES.HIGH
            });
        }
    }

    /**
     * Perform scheduled TLS certificate renewal
     */
    static async performCertificateRenewal() {
        console.log('🔄 Starting scheduled TLS certificate renewal check...');
        
        try {
            // Find certificates expiring within 30 days
            const renewalDate = new Date();
            renewalDate.setDate(renewalDate.getDate() + 30);

            const certsNeedingRenewal = await TLSCertificate.findAll({
                where: {
                    isActive: true,
                    validTo: {
                        [Op.lte]: renewalDate
                    },
                    revokedAt: null
                },
                include: [{
                    model: User,
                    as: 'creator',
                    attributes: ['id', 'username', 'email']
                }]
            });

            console.log(`Found ${certsNeedingRenewal.length} TLS certificates requiring renewal`);

            for (const cert of certsNeedingRenewal) {
                await this.renewTLSCertificate(cert);
            }

            console.log('✅ Scheduled TLS certificate renewal completed');
        } catch (error) {
            console.error('❌ Scheduled TLS certificate renewal failed:', error);
            
            await SecurityAuditLogger.logEvent({
                eventType: SecurityAuditLogger.EVENT_TYPES.TLS_CERT_RENEWED,
                resourceType: SecurityAuditLogger.RESOURCE_TYPES.TLS_CERTIFICATE,
                action: 'Scheduled TLS certificate renewal',
                result: SecurityAuditLogger.RESULTS.ERROR,
                errorMessage: error.message,
                severity: SecurityAuditLogger.SEVERITIES.HIGH
            });
        }
    }

    /**
     * Rotate a specific SSH key
     */
    static async rotateSSHKey(existingKey) {
        try {
            console.log(`🔄 Rotating SSH key: ${existingKey.name} (${existingKey.keyId})`);

            // Generate new key pair
            const newKeyPair = SSHKeyManager.generateKeyPair();
            
            // Generate encryption key and encrypt private key
            const encryptionKey = SSHKeyManager.generateEncryptionKey();
            const encryptedPrivateKey = SSHKeyManager.encryptPrivateKey(
                newKeyPair.privateKey, 
                encryptionKey
            );

            // Create new SSH key
            const newSSHKey = await SSHKey.create({
                keyId: newKeyPair.keyId,
                name: `${existingKey.name} (rotated)`,
                description: `Auto-rotated from ${existingKey.keyId}`,
                publicKey: newKeyPair.publicKey,
                privateKeyEncrypted: encryptedPrivateKey.encrypted,
                encryptionIv: encryptedPrivateKey.iv,
                encryptionAuthTag: encryptedPrivateKey.authTag,
                fingerprint: newKeyPair.fingerprint,
                keySize: SSHKeyManager.KEY_SIZE,
                expiresAt: existingKey.expiresAt,
                createdBy: existingKey.createdBy
            });

            // Mark old key as inactive
            await existingKey.update({
                isActive: false,
                revokedAt: new Date(),
                revocationReason: 'Automatic rotation'
            });

            // Log audit event
            await SecurityAuditLogger.logEvent({
                eventType: SecurityAuditLogger.EVENT_TYPES.SSH_KEY_ROTATED,
                resourceType: SecurityAuditLogger.RESOURCE_TYPES.SSH_KEY,
                resourceId: newKeyPair.keyId,
                userId: existingKey.createdBy,
                action: 'Automatic SSH key rotation',
                details: {
                    oldKeyId: existingKey.keyId,
                    newKeyId: newKeyPair.keyId,
                    rotationReason: 'Scheduled rotation (90 days)'
                },
                severity: SecurityAuditLogger.SEVERITIES.MEDIUM
            });

            console.log(`✅ SSH key rotated successfully: ${existingKey.keyId} → ${newKeyPair.keyId}`);
            
            return newSSHKey;
        } catch (error) {
            console.error(`❌ Failed to rotate SSH key ${existingKey.keyId}:`, error);
            throw error;
        }
    }

    /**
     * Renew a specific TLS certificate
     */
    static async renewTLSCertificate(existingCert) {
        try {
            console.log(`🔄 Renewing TLS certificate: ${existingCert.name} (${existingCert.certificateId})`);

            // Generate new certificate with same parameters
            const newCertData = TLSCertificateManager.generateCertificate({
                commonName: this.extractCommonName(existingCert.subject),
                organization: this.extractOrganization(existingCert.subject),
                validityDays: 365
            });

            // Encrypt private key
            const encryptionPassword = require('./security').generateSecureRandom(32);
            const encryptedPrivateKey = TLSCertificateManager.encryptPrivateKey(
                newCertData.privateKey,
                encryptionPassword
            );

            // Create new certificate
            const newTLSCert = await TLSCertificate.create({
                certificateId: newCertData.certificateId,
                name: `${existingCert.name} (renewed)`,
                description: `Auto-renewed from ${existingCert.certificateId}`,
                certificate: newCertData.certificate,
                privateKeyEncrypted: encryptedPrivateKey,
                publicKey: newCertData.publicKey,
                fingerprint: newCertData.fingerprint,
                serialNumber: newCertData.serialNumber,
                subject: newCertData.subject,
                issuer: newCertData.subject,
                validFrom: newCertData.validFrom,
                validTo: newCertData.validTo,
                createdBy: existingCert.createdBy
            });

            // Mark old certificate as inactive
            await existingCert.update({
                isActive: false,
                revokedAt: new Date(),
                revocationReason: 'Automatic renewal'
            });

            // Log audit event
            await SecurityAuditLogger.logEvent({
                eventType: SecurityAuditLogger.EVENT_TYPES.TLS_CERT_RENEWED,
                resourceType: SecurityAuditLogger.RESOURCE_TYPES.TLS_CERTIFICATE,
                resourceId: newCertData.certificateId,
                userId: existingCert.createdBy,
                action: 'Automatic TLS certificate renewal',
                details: {
                    oldCertId: existingCert.certificateId,
                    newCertId: newCertData.certificateId,
                    renewalReason: 'Expiring within 30 days'
                },
                severity: SecurityAuditLogger.SEVERITIES.MEDIUM
            });

            console.log(`✅ TLS certificate renewed successfully: ${existingCert.certificateId} → ${newCertData.certificateId}`);
            
            return newTLSCert;
        } catch (error) {
            console.error(`❌ Failed to renew TLS certificate ${existingCert.certificateId}:`, error);
            throw error;
        }
    }

    /**
     * Manually rotate SSH key
     */
    static async manualRotateSSHKey(keyId, userId) {
        const existingKey = await SSHKey.findOne({
            where: {
                keyId,
                createdBy: userId,
                isActive: true
            }
        });

        if (!existingKey) {
            throw new Error('SSH key not found or not accessible');
        }

        return this.rotateSSHKey(existingKey);
    }

    /**
     * Manually renew TLS certificate
     */
    static async manualRenewTLSCertificate(certificateId, userId) {
        const existingCert = await TLSCertificate.findOne({
            where: {
                certificateId,
                createdBy: userId,
                isActive: true
            }
        });

        if (!existingCert) {
            throw new Error('TLS certificate not found or not accessible');
        }

        return this.renewTLSCertificate(existingCert);
    }

    /**
     * Get rotation statistics
     */
    static async getRotationStats() {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        const [sshKeysRotated, tlsCertsRenewed, expiringSoon] = await Promise.all([
            SSHKey.count({
                where: {
                    revokedAt: {
                        [Op.gte]: thirtyDaysAgo
                    },
                    revocationReason: 'Automatic rotation'
                }
            }),
            TLSCertificate.count({
                where: {
                    revokedAt: {
                        [Op.gte]: thirtyDaysAgo
                    },
                    revocationReason: 'Automatic renewal'
                }
            }),
            this.getItemsExpiringSoon()
        ]);

        return {
            sshKeysRotatedLast30Days: sshKeysRotated,
            tlsCertsRenewedLast30Days: tlsCertsRenewed,
            itemsExpiringSoon
        };
    }

    /**
     * Get items expiring soon
     */
    static async getItemsExpiringSoon() {
        const thirtyDaysFromNow = new Date();
        thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

        const ninetyDaysAgo = new Date();
        ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);

        const [expiringSshKeys, expiringCerts] = await Promise.all([
            SSHKey.count({
                where: {
                    isActive: true,
                    createdAt: {
                        [Op.lte]: ninetyDaysAgo
                    }
                }
            }),
            TLSCertificate.count({
                where: {
                    isActive: true,
                    validTo: {
                        [Op.lte]: thirtyDaysFromNow
                    }
                }
            })
        ]);

        return {
            sshKeysNeedingRotation: expiringSshKeys,
            tlsCertsNeedingRenewal: expiringCerts
        };
    }

    /**
     * Extract common name from certificate subject
     */
    static extractCommonName(subject) {
        const cnMatch = subject.match(/CN=([^,]+)/);
        return cnMatch ? cnMatch[1] : 'localhost';
    }

    /**
     * Extract organization from certificate subject
     */
    static extractOrganization(subject) {
        const oMatch = subject.match(/O=([^,]+)/);
        return oMatch ? oMatch[1] : 'Organization';
    }

    /**
     * Clean up revoked keys and certificates older than retention period
     */
    static async cleanupOldItems(retentionDays = 365) {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

        const [deletedKeys, deletedCerts] = await Promise.all([
            SSHKey.destroy({
                where: {
                    isActive: false,
                    revokedAt: {
                        [Op.lt]: cutoffDate
                    }
                }
            }),
            TLSCertificate.destroy({
                where: {
                    isActive: false,
                    revokedAt: {
                        [Op.lt]: cutoffDate
                    }
                }
            })
        ]);

        console.log(`Cleaned up ${deletedKeys} old SSH keys and ${deletedCerts} old TLS certificates`);
        
        return {
            deletedKeys,
            deletedCerts
        };
    }
}

module.exports = KeyRotationManager;