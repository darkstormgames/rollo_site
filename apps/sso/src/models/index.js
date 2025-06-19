const sequelize = require('../config/sequelize');
const User = require('./User');
const RefreshToken = require('./RefreshToken');
const JwtSecret = require('./JwtSecret');
const UserSession = require('./UserSession');
const SsoSite = require('./SsoSite');
const UserSitePermission = require('./UserSitePermission');
const SSHKey = require('./SSHKey');
const TLSCertificate = require('./TLSCertificate');
const SecurityAuditLog = require('./SecurityAuditLog');

// Define associations
User.hasMany(RefreshToken, { foreignKey: 'user_id', as: 'refreshTokens' });
RefreshToken.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

User.hasMany(UserSession, { foreignKey: 'user_id', as: 'sessions' });
UserSession.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

User.belongsToMany(SsoSite, { 
    through: UserSitePermission, 
    foreignKey: 'user_id',
    otherKey: 'site_id',
    as: 'sites'
});

SsoSite.belongsToMany(User, { 
    through: UserSitePermission, 
    foreignKey: 'site_id',
    otherKey: 'user_id',
    as: 'users'
});

User.hasMany(UserSitePermission, { foreignKey: 'user_id', as: 'sitePermissions' });
UserSitePermission.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

SsoSite.hasMany(UserSitePermission, { foreignKey: 'site_id', as: 'userPermissions' });
UserSitePermission.belongsTo(SsoSite, { foreignKey: 'site_id', as: 'site' });

// Security-related associations
User.hasMany(SSHKey, { foreignKey: 'created_by', as: 'sshKeys' });
SSHKey.belongsTo(User, { foreignKey: 'created_by', as: 'creator' });

User.hasMany(TLSCertificate, { foreignKey: 'created_by', as: 'tlsCertificates' });
TLSCertificate.belongsTo(User, { foreignKey: 'created_by', as: 'creator' });

User.hasMany(SecurityAuditLog, { foreignKey: 'user_id', as: 'auditLogs' });
SecurityAuditLog.belongsTo(User, { foreignKey: 'user_id', as: 'user' });

// Export all models and sequelize instance
module.exports = {
    sequelize,
    User,
    RefreshToken,
    JwtSecret,
    UserSession,
    SsoSite,
    UserSitePermission,
    SSHKey,
    TLSCertificate,
    SecurityAuditLog
};