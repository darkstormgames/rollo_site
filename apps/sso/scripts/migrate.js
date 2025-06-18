require('dotenv').config();
const { sequelize, SsoSite } = require('../src/models');
const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');

async function runMigration() {
    // First, create database and tables using raw SQL if needed
    const connection = await mysql.createConnection({
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 3306,
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || '',
        multipleStatements: true
    });

    try {
        console.log('Connected to MySQL server');
        
        // Read and execute schema to ensure database exists
        const schemaPath = path.join(__dirname, 'schema.sql');
        const schema = fs.readFileSync(schemaPath, 'utf8');
        
        await connection.execute(schema);
        console.log('Database schema created successfully');
        
    } catch (error) {
        console.error('Schema creation failed:', error);
        throw error;
    } finally {
        await connection.end();
    }

    // Now use Sequelize to sync models and insert data
    try {
        await sequelize.authenticate();
        console.log('Sequelize connected to database');
        
        // Sync all models
        await sequelize.sync({ force: false, alter: true });
        console.log('Database models synchronized');
        
        // Insert default site registration for Rollo Site
        await SsoSite.findOrCreate({
            where: { site_name: 'Rollo Site' },
            defaults: {
                site_name: 'Rollo Site',
                site_url: 'http://localhost:4200',
                api_key_hash: require('crypto').createHash('sha256').update('rollo-site-default-key').digest('hex'),
                access_level_required: 'basic'
            }
        });
        
        console.log('Default site registration completed');
        
    } catch (error) {
        console.error('Sequelize migration failed:', error);
        throw error;
    } finally {
        await sequelize.close();
    }
}

if (require.main === module) {
    runMigration().then(() => {
        console.log('Migration completed successfully');
        process.exit(0);
    }).catch(error => {
        console.error('Migration failed:', error);
        process.exit(1);
    });
}

module.exports = { runMigration };