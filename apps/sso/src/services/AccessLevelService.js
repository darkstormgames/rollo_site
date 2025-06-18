const { User, SsoSite, UserSitePermission } = require('../models');

class AccessLevelService {
    static ACCESS_LEVELS = {
        basic: 1,
        standard: 2,
        premium: 3,
        admin: 4
    };

    /**
     * Check if user has sufficient access level for a site
     */
    static hasAccessToSite(userAccessLevel, requiredAccessLevel) {
        const userLevel = this.ACCESS_LEVELS[userAccessLevel] || 0;
        const requiredLevel = this.ACCESS_LEVELS[requiredAccessLevel] || 0;
        return userLevel >= requiredLevel;
    }

    /**
     * Get all sites accessible to a user based on their access level
     */
    static async getAccessibleSites(userId) {
        const user = await User.findByPk(userId);
        if (!user) {
            throw new Error('User not found');
        }

        const sites = await SsoSite.findAll({
            where: {
                is_active: true
            }
        });

        return sites.filter(site => 
            this.hasAccessToSite(user.access_level, site.access_level_required)
        );
    }

    /**
     * Check if user can access a specific site
     */
    static async canAccessSite(userId, siteId) {
        const user = await User.findByPk(userId);
        const site = await SsoSite.findByPk(siteId);

        if (!user || !site) {
            return false;
        }

        return this.hasAccessToSite(user.access_level, site.access_level_required);
    }

    /**
     * Update user access level (admin only)
     */
    static async updateUserAccessLevel(adminUserId, targetUserId, newAccessLevel) {
        const admin = await User.findByPk(adminUserId);
        
        if (!admin || admin.access_level !== 'admin') {
            throw new Error('Insufficient permissions: Admin access required');
        }

        if (!this.ACCESS_LEVELS[newAccessLevel]) {
            throw new Error('Invalid access level');
        }

        const targetUser = await User.findByPk(targetUserId);
        if (!targetUser) {
            throw new Error('Target user not found');
        }

        await targetUser.update({ access_level: newAccessLevel });
        return targetUser;
    }

    /**
     * Update site access level requirement (admin only)
     */
    static async updateSiteAccessLevel(adminUserId, siteId, requiredAccessLevel) {
        const admin = await User.findByPk(adminUserId);
        
        if (!admin || admin.access_level !== 'admin') {
            throw new Error('Insufficient permissions: Admin access required');
        }

        if (!this.ACCESS_LEVELS[requiredAccessLevel]) {
            throw new Error('Invalid access level');
        }

        const site = await SsoSite.findByPk(siteId);
        if (!site) {
            throw new Error('Site not found');
        }

        await site.update({ access_level_required: requiredAccessLevel });
        return site;
    }

    /**
     * Get users by access level (admin only)
     */
    static async getUsersByAccessLevel(adminUserId, accessLevel = null) {
        const admin = await User.findByPk(adminUserId);
        
        if (!admin || admin.access_level !== 'admin') {
            throw new Error('Insufficient permissions: Admin access required');
        }

        const whereClause = { is_active: true };
        if (accessLevel) {
            whereClause.access_level = accessLevel;
        }

        return await User.findAll({
            where: whereClause,
            attributes: ['id', 'username', 'email', 'first_name', 'last_name', 'access_level', 'created_at']
        });
    }
}

module.exports = AccessLevelService;