const { DataTypes } = require('sequelize');
const sequelize = require('../config/sequelize');

const SsoSite = sequelize.define('SsoSite', {
    id: {
        type: DataTypes.INTEGER,
        primaryKey: true,
        autoIncrement: true
    },
    site_name: {
        type: DataTypes.STRING(100),
        allowNull: false,
        unique: true
    },
    site_url: {
        type: DataTypes.STRING(255),
        allowNull: false
    },
    api_key_hash: {
        type: DataTypes.STRING(255),
        allowNull: false
    },
    access_level_required: {
        type: DataTypes.ENUM('admin', 'premium', 'standard', 'basic'),
        allowNull: false,
        defaultValue: 'basic'
    },
    is_active: {
        type: DataTypes.BOOLEAN,
        defaultValue: true
    }
}, {
    tableName: 'sso_sites',
    updatedAt: false
});

module.exports = SsoSite;