const request = require('supertest');
const { Sequelize } = require('sequelize');
const app = require('../server');

// Create test database connection
const testSequelize = new Sequelize({
    dialect: 'sqlite',
    storage: ':memory:',
    logging: false
});

// Override the sequelize instance for testing
const originalSequelize = require('../src/models').sequelize;

describe('Security API', () => {
    let server;
    let testUser;
    let authToken;

    beforeAll(async () => {
        // Use test database
        process.env.NODE_ENV = 'test';
        
        // Replace sequelize with test instance
        const models = require('../src/models');
        Object.setPrototypeOf(models.sequelize, testSequelize);
        
        // Initialize models with test database
        const { User, SSHKey, TLSCertificate, SecurityAuditLog } = models;
        
        await testSequelize.sync({ force: true });
        
        // Create test user
        testUser = await User.create({
            username: 'testuser',
            email: 'test@example.com',
            password_hash: '$2b$12$hashed.password.here',
            first_name: 'Test',
            last_name: 'User',
            access_level: 'admin'
        });

        // Generate auth token for testing
        const SecurityUtils = require('../src/utils/security');
        authToken = SecurityUtils.generateToken({
            userId: testUser.id,
            username: testUser.username
        }, 'test-secret');
    });

    afterAll(async () => {
        await testSequelize.close();
    });

    describe('SSH Key Management', () => {
        describe('POST /api/security/keys/generate', () => {
            it('should generate SSH key pair with valid data', async () => {
                const response = await request(app)
                    .post('/api/security/keys/generate')
                    .set('Authorization', `Bearer ${authToken}`)
                    .send({
                        name: 'Test SSH Key',
                        description: 'Test key for unit tests',
                        expiresInDays: 90
                    });

                console.log('Response status:', response.status);
                console.log('Response body:', response.body);

                expect(response.status).toBe(201);
                expect(response.body.message).toBe('SSH key pair generated successfully');
                expect(response.body.key).toBeDefined();
                expect(response.body.key.keyId).toBeDefined();
                expect(response.body.key.name).toBe('Test SSH Key');
                expect(response.body.key.publicKey).toMatch(/^ssh-rsa/);
                expect(response.body.key.fingerprint).toMatch(/^[a-f0-9:]+$/);
                expect(response.body.key.keySize).toBe(4096);
            });
        });
    });
});