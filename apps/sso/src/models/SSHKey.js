const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const SSHKey = sequelize.define('SSHKey', {
    id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true
    },
    keyId: {
        type: DataTypes.STRING(36),
        allowNull: false,
        unique: true,
        field: 'key_id'
    },
    name: {
        type: DataTypes.STRING(255),
        allowNull: false
    },
    description: {
        type: DataTypes.TEXT,
        allowNull: true
    },
    publicKey: {
        type: DataTypes.TEXT,
        allowNull: false,
        field: 'public_key'
    },
    privateKeyEncrypted: {
        type: DataTypes.TEXT,
        allowNull: false,
        field: 'private_key_encrypted'
    },
    encryptionIv: {
        type: DataTypes.STRING(32),
        allowNull: false,
        field: 'encryption_iv'
    },
    encryptionAuthTag: {
        type: DataTypes.STRING(32),
        allowNull: false,
        field: 'encryption_auth_tag'
    },
    fingerprint: {
        type: DataTypes.STRING(255),
        allowNull: false,
        unique: true
    },
    keySize: {
        type: DataTypes.INTEGER,
        allowNull: false,
        defaultValue: 4096,
        field: 'key_size'
    },
    isActive: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: true,
        field: 'is_active'
    },
    lastUsed: {
        type: DataTypes.DATE,
        allowNull: true,
        field: 'last_used'
    },
    expiresAt: {
        type: DataTypes.DATE,
        allowNull: true,
        field: 'expires_at'
    },
    createdBy: {
        type: DataTypes.INTEGER,
        allowNull: false,
        field: 'created_by'
    },
    createdAt: {
        type: DataTypes.DATE,
        allowNull: false,
        defaultValue: DataTypes.NOW,
        field: 'created_at'
    },
    updatedAt: {
        type: DataTypes.DATE,
        allowNull: false,
        defaultValue: DataTypes.NOW,
        field: 'updated_at'
    },
    revokedAt: {
        type: DataTypes.DATE,
        allowNull: true,
        field: 'revoked_at'
    },
    revokedBy: {
        type: DataTypes.INTEGER,
        allowNull: true,
        field: 'revoked_by'
    },
    revocationReason: {
        type: DataTypes.STRING(255),
        allowNull: true,
        field: 'revocation_reason'
    }
}, {
    tableName: 'ssh_keys',
    timestamps: false,
    indexes: [
        {
            fields: ['key_id']
        },
        {
            fields: ['fingerprint']
        },
        {
            fields: ['is_active']
        },
        {
            fields: ['created_by']
        },
        {
            fields: ['expires_at']
        }
    ]
});

module.exports = SSHKey;