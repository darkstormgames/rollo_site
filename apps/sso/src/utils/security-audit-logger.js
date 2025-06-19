const { SecurityAuditLog, User, sequelize } = require('../models');
const { Op } = require('sequelize');

class SecurityAuditLogger {
    static EVENT_TYPES = {
        SSH_KEY_GENERATED: 'ssh_key_generated',
        SSH_KEY_DEPLOYED: 'ssh_key_deployed',
        SSH_KEY_REVOKED: 'ssh_key_revoked',
        SSH_KEY_ROTATED: 'ssh_key_rotated',
        TLS_CERT_GENERATED: 'tls_cert_generated',
        TLS_CERT_REVOKED: 'tls_cert_revoked',
        TLS_CERT_RENEWED: 'tls_cert_renewed',
        SECURITY_CONFIG_CHANGED: 'security_config_changed',
        AUTH_FAILURE: 'auth_failure',
        SUSPICIOUS_ACTIVITY: 'suspicious_activity'
    };

    static RESOURCE_TYPES = {
        SSH_KEY: 'ssh_key',
        TLS_CERTIFICATE: 'tls_certificate',
        SECURITY_CONFIG: 'security_config',
        USER_SESSION: 'user_session'
    };

    static SEVERITIES = {
        LOW: 'LOW',
        MEDIUM: 'MEDIUM',
        HIGH: 'HIGH',
        CRITICAL: 'CRITICAL'
    };

    static RESULTS = {
        SUCCESS: 'SUCCESS',
        FAILURE: 'FAILURE',
        ERROR: 'ERROR'
    };

    /**
     * Log security audit event
     */
    static async logEvent({
        eventType,
        resourceType,
        resourceId = null,
        userId = null,
        ipAddress = null,
        userAgent = null,
        action,
        result = this.RESULTS.SUCCESS,
        details = null,
        errorMessage = null,
        severity = this.SEVERITIES.LOW
    }) {
        try {
            const auditLog = await SecurityAuditLog.create({
                eventType,
                resourceType,
                resourceId,
                userId,
                ipAddress,
                userAgent,
                action,
                result,
                details,
                errorMessage,
                severity
            });

            // Log to console for immediate visibility
            console.log(`[SECURITY AUDIT] ${eventType} - ${action} - ${result}`, {
                resourceType,
                resourceId,
                userId,
                severity
            });

            return auditLog;
        } catch (error) {
            console.error('Failed to log security audit event:', error);
            // Don't throw - audit logging should not break application flow
        }
    }

    /**
     * Log SSH key generation
     */
    static async logSSHKeyGenerated(keyId, userId, ipAddress, userAgent) {
        return this.logEvent({
            eventType: this.EVENT_TYPES.SSH_KEY_GENERATED,
            resourceType: this.RESOURCE_TYPES.SSH_KEY,
            resourceId: keyId,
            userId,
            ipAddress,
            userAgent,
            action: 'Generate SSH key pair',
            severity: this.SEVERITIES.MEDIUM
        });
    }

    /**
     * Log SSH key deployment
     */
    static async logSSHKeyDeployed(keyId, targetHost, userId, ipAddress, userAgent, success = true) {
        return this.logEvent({
            eventType: this.EVENT_TYPES.SSH_KEY_DEPLOYED,
            resourceType: this.RESOURCE_TYPES.SSH_KEY,
            resourceId: keyId,
            userId,
            ipAddress,
            userAgent,
            action: `Deploy SSH key to ${targetHost}`,
            result: success ? this.RESULTS.SUCCESS : this.RESULTS.FAILURE,
            details: { targetHost },
            severity: this.SEVERITIES.MEDIUM
        });
    }

    /**
     * Log SSH key revocation
     */
    static async logSSHKeyRevoked(keyId, reason, userId, ipAddress, userAgent) {
        return this.logEvent({
            eventType: this.EVENT_TYPES.SSH_KEY_REVOKED,
            resourceType: this.RESOURCE_TYPES.SSH_KEY,
            resourceId: keyId,
            userId,
            ipAddress,
            userAgent,
            action: 'Revoke SSH key',
            details: { reason },
            severity: this.SEVERITIES.HIGH
        });
    }

    /**
     * Log TLS certificate generation
     */
    static async logTLSCertGenerated(certId, commonName, userId, ipAddress, userAgent) {
        return this.logEvent({
            eventType: this.EVENT_TYPES.TLS_CERT_GENERATED,
            resourceType: this.RESOURCE_TYPES.TLS_CERTIFICATE,
            resourceId: certId,
            userId,
            ipAddress,
            userAgent,
            action: 'Generate TLS certificate',
            details: { commonName },
            severity: this.SEVERITIES.MEDIUM
        });
    }

    /**
     * Log authentication failure
     */
    static async logAuthFailure(reason, ipAddress, userAgent, severity = this.SEVERITIES.MEDIUM) {
        return this.logEvent({
            eventType: this.EVENT_TYPES.AUTH_FAILURE,
            resourceType: this.RESOURCE_TYPES.USER_SESSION,
            ipAddress,
            userAgent,
            action: 'Authentication attempt',
            result: this.RESULTS.FAILURE,
            errorMessage: reason,
            severity
        });
    }

    /**
     * Log suspicious activity
     */
    static async logSuspiciousActivity(description, ipAddress, userAgent, details = null) {
        return this.logEvent({
            eventType: this.EVENT_TYPES.SUSPICIOUS_ACTIVITY,
            resourceType: this.RESOURCE_TYPES.USER_SESSION,
            ipAddress,
            userAgent,
            action: 'Suspicious activity detected',
            details,
            errorMessage: description,
            severity: this.SEVERITIES.HIGH
        });
    }

    /**
     * Get audit logs with filtering
     */
    static async getAuditLogs({
        eventType = null,
        resourceType = null,
        userId = null,
        severity = null,
        result = null,
        startDate = null,
        endDate = null,
        limit = 100,
        offset = 0
    } = {}) {
        const where = {};
        
        if (eventType) where.eventType = eventType;
        if (resourceType) where.resourceType = resourceType;
        if (userId) where.userId = userId;
        if (severity) where.severity = severity;
        if (result) where.result = result;
        
        if (startDate || endDate) {
            where.createdAt = {};
            if (startDate) where.createdAt[Op.gte] = startDate;
            if (endDate) where.createdAt[Op.lte] = endDate;
        }

        return SecurityAuditLog.findAndCountAll({
            where,
            order: [['createdAt', 'DESC']],
            limit,
            offset,
            include: [{
                model: User,
                as: 'user',
                attributes: ['id', 'username', 'email']
            }]
        });
    }

    /**
     * Get security metrics
     */
    static async getSecurityMetrics(days = 30) {
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);

        const [
            totalEvents,
            failureEvents,
            criticalEvents,
            eventsByType
        ] = await Promise.all([
            SecurityAuditLog.count({
                where: {
                    createdAt: {
                        [Op.gte]: startDate
                    }
                }
            }),
            SecurityAuditLog.count({
                where: {
                    result: this.RESULTS.FAILURE,
                    createdAt: {
                        [Op.gte]: startDate
                    }
                }
            }),
            SecurityAuditLog.count({
                where: {
                    severity: this.SEVERITIES.CRITICAL,
                    createdAt: {
                        [Op.gte]: startDate
                    }
                }
            }),
            SecurityAuditLog.findAll({
                attributes: [
                    'eventType',
                    [sequelize.fn('COUNT', sequelize.col('id')), 'count']
                ],
                where: {
                    createdAt: {
                        [Op.gte]: startDate
                    }
                },
                group: ['eventType'],
                order: [[sequelize.fn('COUNT', sequelize.col('id')), 'DESC']]
            })
        ]);

        return {
            totalEvents,
            failureEvents,
            criticalEvents,
            failureRate: totalEvents > 0 ? (failureEvents / totalEvents * 100).toFixed(2) : 0,
            eventsByType: eventsByType.map(event => ({
                type: event.eventType,
                count: parseInt(event.getDataValue('count'))
            }))
        };
    }

    /**
     * Clean old audit logs (keep for specified days)
     */
    static async cleanOldLogs(retentionDays = 365) {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

        const deletedCount = await SecurityAuditLog.destroy({
            where: {
                createdAt: {
                    [Op.lt]: cutoffDate
                }
            }
        });

        console.log(`Cleaned ${deletedCount} old audit log entries`);
        return deletedCount;
    }
}

module.exports = SecurityAuditLogger;