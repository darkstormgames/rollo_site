const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const JwtSecret = sequelize.define('JwtSecret', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    key_id: {
        type: DataTypes.STRING(36),
        allowNull: false,
        unique: true
    },
    secret_hash: {
        type: DataTypes.STRING(255),
        allowNull: false
    },
    type: {
        type: DataTypes.ENUM('access', 'refresh'),
        allowNull: false
    },
    is_active: {
        type: DataTypes.BOOLEAN,
        defaultValue: true
    },
    expires_at: {
        type: DataTypes.DATE,
        allowNull: true
    }
}, {
    tableName: 'jwt_secrets',
    updatedAt: false
});

module.exports = JwtSecret;