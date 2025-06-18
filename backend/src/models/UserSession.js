const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const UserSession = sequelize.define('UserSession', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    user_id: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: {
            model: 'users',
            key: 'id'
        }
    },
    session_id: {
        type: DataTypes.STRING(255),
        allowNull: false,
        unique: true
    },
    ip_address: {
        type: DataTypes.STRING(45),
        allowNull: true
    },
    user_agent: {
        type: DataTypes.TEXT,
        allowNull: true
    },
    last_accessed: {
        type: DataTypes.DATE,
        defaultValue: DataTypes.NOW
    },
    expires_at: {
        type: DataTypes.DATE,
        allowNull: false
    }
}, {
    tableName: 'user_sessions',
    updatedAt: 'last_accessed',
    indexes: [
        {
            fields: ['user_id']
        },
        {
            fields: ['session_id']
        },
        {
            fields: ['expires_at']
        }
    ]
});

module.exports = UserSession;