const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const User = sequelize.define('User', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    username: {
        type: DataTypes.STRING(50),
        allowNull: false,
        unique: true
    },
    email: {
        type: DataTypes.STRING(100),
        allowNull: false,
        unique: true
    },
    password_hash: {
        type: DataTypes.STRING(255),
        allowNull: false
    },
    first_name: {
        type: DataTypes.STRING(50),
        allowNull: true
    },
    last_name: {
        type: DataTypes.STRING(50),
        allowNull: true
    },
    access_level: {
        type: DataTypes.ENUM('admin', 'premium', 'standard', 'basic'),
        allowNull: false,
        defaultValue: 'basic'
    },
    is_active: {
        type: DataTypes.BOOLEAN,
        defaultValue: true
    }
}, {
    tableName: 'users',
    indexes: [
        {
            fields: ['email']
        },
        {
            fields: ['username']
        },
        {
            fields: ['is_active']
        },
        {
            fields: ['access_level']
        }
    ]
});

module.exports = User;