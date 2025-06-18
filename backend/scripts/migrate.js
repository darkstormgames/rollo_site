require('dotenv').config();
const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');

async function runMigration() {
    const connection = await mysql.createConnection({
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 3306,
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || '',
        multipleStatements: true
    });

    try {
        console.log('Connected to MySQL server');
        
        // Read and execute schema
        const schemaPath = path.join(__dirname, 'schema.sql');
        const schema = fs.readFileSync(schemaPath, 'utf8');
        
        await connection.execute(schema);
        console.log('Database schema created successfully');
        
        // Insert default site registration for Rollo Site
        await connection.execute(`
            USE rollo_sso;
            INSERT IGNORE INTO sso_sites (site_name, site_url, api_key_hash) 
            VALUES ('Rollo Site', 'http://localhost:4200', SHA2('rollo-site-default-key', 256));
        `);
        
        console.log('Default site registration completed');
        
    } catch (error) {
        console.error('Migration failed:', error);
        process.exit(1);
    } finally {
        await connection.end();
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