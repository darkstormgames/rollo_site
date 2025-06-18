const { Sequelize } = require('sequelize');

// Create Sequelize instance
const sequelize = new Sequelize(
    process.env.DB_NAME || 'rollo_sso',
    process.env.DB_USER || 'root',
    process.env.DB_PASSWORD || '',
    {
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 3306,
        dialect: 'mysql',
        logging: process.env.NODE_ENV === 'development' ? console.log : false,
        pool: {
            max: 10,
            min: 0,
            acquire: 60000,
            idle: 10000
        },
        define: {
            underscored: true,
            timestamps: true,
            createdAt: 'created_at',
            updatedAt: 'updated_at'
        }
    }
);

module.exports = sequelize;