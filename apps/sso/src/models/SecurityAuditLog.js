const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const SecurityAuditLog = sequelize.define('SecurityAuditLog', {
    id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true
    },
    eventType: {
        type: DataTypes.STRING(100),
        allowNull: false,
        field: 'event_type'
    },
    resourceType: {
        type: DataTypes.STRING(50),
        allowNull: false,
        field: 'resource_type'
    },
    resourceId: {
        type: DataTypes.STRING(255),
        allowNull: true,
        field: 'resource_id'
    },
    userId: {
        type: DataTypes.INTEGER,
        allowNull: true,
        field: 'user_id'
    },
    ipAddress: {
        type: DataTypes.STRING(45),
        allowNull: true,
        field: 'ip_address'
    },
    userAgent: {
        type: DataTypes.TEXT,
        allowNull: true,
        field: 'user_agent'
    },
    action: {
        type: DataTypes.STRING(100),
        allowNull: false
    },
    result: {
        type: DataTypes.ENUM('SUCCESS', 'FAILURE', 'ERROR'),
        allowNull: false,
        defaultValue: 'SUCCESS'
    },
    details: {
        type: DataTypes.JSON,
        allowNull: true
    },
    errorMessage: {
        type: DataTypes.TEXT,
        allowNull: true,
        field: 'error_message'
    },
    severity: {
        type: DataTypes.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'),
        allowNull: false,
        defaultValue: 'LOW'
    },
    createdAt: {
        type: DataTypes.DATE,
        allowNull: false,
        defaultValue: DataTypes.NOW,
        field: 'created_at'
    }
}, {
    tableName: 'security_audit_logs',
    timestamps: false,
    indexes: [
        {
            fields: ['event_type']
        },
        {
            fields: ['resource_type']
        },
        {
            fields: ['resource_id']
        },
        {
            fields: ['user_id']
        },
        {
            fields: ['result']
        },
        {
            fields: ['severity']
        },
        {
            fields: ['created_at']
        },
        {
            fields: ['ip_address']
        }
    ]
});

module.exports = SecurityAuditLog;