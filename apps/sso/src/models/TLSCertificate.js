const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const TLSCertificate = sequelize.define('TLSCertificate', {
    id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true
    },
    certificateId: {
        type: DataTypes.STRING(36),
        allowNull: false,
        unique: true,
        field: 'certificate_id'
    },
    name: {
        type: DataTypes.STRING(255),
        allowNull: false
    },
    description: {
        type: DataTypes.TEXT,
        allowNull: true
    },
    certificate: {
        type: DataTypes.TEXT,
        allowNull: false
    },
    privateKeyEncrypted: {
        type: DataTypes.TEXT,
        allowNull: false,
        field: 'private_key_encrypted'
    },
    publicKey: {
        type: DataTypes.TEXT,
        allowNull: false,
        field: 'public_key'
    },
    fingerprint: {
        type: DataTypes.STRING(255),
        allowNull: false,
        unique: true
    },
    serialNumber: {
        type: DataTypes.STRING(255),
        allowNull: false,
        field: 'serial_number'
    },
    subject: {
        type: DataTypes.TEXT,
        allowNull: false
    },
    issuer: {
        type: DataTypes.TEXT,
        allowNull: false
    },
    validFrom: {
        type: DataTypes.DATE,
        allowNull: false,
        field: 'valid_from'
    },
    validTo: {
        type: DataTypes.DATE,
        allowNull: false,
        field: 'valid_to'
    },
    keySize: {
        type: DataTypes.INTEGER,
        allowNull: false,
        defaultValue: 2048,
        field: 'key_size'
    },
    algorithm: {
        type: DataTypes.STRING(50),
        allowNull: false,
        defaultValue: 'RSA'
    },
    isCA: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: false,
        field: 'is_ca'
    },
    isActive: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: true,
        field: 'is_active'
    },
    caCertificateId: {
        type: DataTypes.STRING(36),
        allowNull: true,
        field: 'ca_certificate_id'
    },
    lastUsed: {
        type: DataTypes.DATE,
        allowNull: true,
        field: 'last_used'
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
    tableName: 'tls_certificates',
    timestamps: false,
    indexes: [
        {
            fields: ['certificate_id']
        },
        {
            fields: ['fingerprint']
        },
        {
            fields: ['serial_number']
        },
        {
            fields: ['is_active']
        },
        {
            fields: ['is_ca']
        },
        {
            fields: ['created_by']
        },
        {
            fields: ['valid_to']
        },
        {
            fields: ['ca_certificate_id']
        }
    ]
});

module.exports = TLSCertificate;