const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const UserSitePermission = sequelize.define('UserSitePermission', {
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
    site_id: {
        type: DataTypes.INTEGER,
        allowNull: false,
        references: {
            model: 'sso_sites',
            key: 'id'
        }
    },
    role: {
        type: DataTypes.STRING(50),
        defaultValue: 'user'
    },
    granted_at: {
        type: DataTypes.DATE,
        defaultValue: DataTypes.NOW
    }
}, {
    tableName: 'user_site_permissions',
    timestamps: false,
    indexes: [
        {
            unique: true,
            fields: ['user_id', 'site_id']
        }
    ]
});

module.exports = UserSitePermission;