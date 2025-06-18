const { sequelize } = require('../models');

// Legacy wrapper for backward compatibility during transition
class Database {
    constructor() {
        this.sequelize = sequelize;
    }

    async query(sql, params = []) {
        try {
            const [rows] = await sequelize.query(sql, { 
                replacements: params,
                type: sequelize.QueryTypes.SELECT 
            });
            return rows;
        } catch (error) {
            console.error('Database query error:', error);
            throw error;
        }
    }

    async transaction(callback) {
        const transaction = await sequelize.transaction();
        try {
            const result = await callback(transaction);
            await transaction.commit();
            return result;
        } catch (error) {
            await transaction.rollback();
            throw error;
        }
    }

    async close() {
        await sequelize.close();
    }
}

// For legacy compatibility
module.exports = new Database();