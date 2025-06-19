const request = require('supertest');
const app = require('../server');
const { sequelize, User, SSHKey, TLSCertificate } = require('../src/models');

describe('Security API', () => {
    let server;
    let testUser;
    let authToken;

    beforeAll(async () => {
        // Use test database
        process.env.NODE_ENV = 'test';
        
        await sequelize.sync({ force: true });
        
        // Create test user
        testUser = await User.create({
            username: 'testuser',
            email: 'test@example.com',
            password: '$2b$12$hashed.password.here',
            firstName: 'Test',
            lastName: 'User',
            accessLevel: 'admin'
        });

        // Generate auth token for testing
        const SecurityUtils = require('../src/utils/security');
        authToken = SecurityUtils.generateToken({
            userId: testUser.id,
            username: testUser.username
        }, 'test-secret');
    });

    afterAll(async () => {
        await sequelize.close();
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
                    })
                    .expect(201);

                expect(response.body.message).toBe('SSH key pair generated successfully');
                expect(response.body.key).toBeDefined();
                expect(response.body.key.keyId).toBeDefined();
                expect(response.body.key.name).toBe('Test SSH Key');
                expect(response.body.key.publicKey).toMatch(/^ssh-rsa/);
                expect(response.body.key.fingerprint).toMatch(/^[a-f0-9:]+$/);
                expect(response.body.key.keySize).toBe(4096);
            });

            it('should reject invalid name', async () => {
                const response = await request(app)
                    .post('/api/security/keys/generate')
                    .set('Authorization', `Bearer ${authToken}`)
                    .send({
                        name: '',
                        description: 'Test key'
                    })
                    .expect(400);

                expect(response.body.error).toBe('Validation failed');
            });

            it('should reject unauthorized requests', async () => {
                await request(app)
                    .post('/api/security/keys/generate')
                    .send({
                        name: 'Test SSH Key'
                    })
                    .expect(401);
            });
        });

        describe('GET /api/security/keys', () => {
            beforeAll(async () => {
                // Create test SSH key
                await SSHKey.create({
                    keyId: 'test-key-id-1',
                    name: 'Test Key 1',
                    description: 'Test description',
                    publicKey: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... test-key',
                    privateKeyEncrypted: 'encrypted-private-key',
                    encryptionIv: 'test-iv',
                    encryptionAuthTag: 'test-auth-tag',
                    fingerprint: 'aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99',
                    keySize: 4096,
                    createdBy: testUser.id
                });
            });

            it('should list SSH keys for authenticated user', async () => {
                const response = await request(app)
                    .get('/api/security/keys')
                    .set('Authorization', `Bearer ${authToken}`)
                    .expect(200);

                expect(response.body.keys).toBeDefined();
                expect(Array.isArray(response.body.keys)).toBe(true);
                expect(response.body.pagination).toBeDefined();
                expect(response.body.pagination.total).toBeGreaterThan(0);
            });

            it('should filter active keys only', async () => {
                const response = await request(app)
                    .get('/api/security/keys?active=true')
                    .set('Authorization', `Bearer ${authToken}`)
                    .expect(200);

                expect(response.body.keys).toBeDefined();
                response.body.keys.forEach(key => {
                    expect(key.isActive).toBe(true);
                });
            });
        });

        describe('DELETE /api/security/keys/:keyId', () => {
            let testKeyId;

            beforeAll(async () => {
                const sshKey = await SSHKey.create({
                    keyId: 'test-key-for-deletion',
                    name: 'Key to Delete',
                    description: 'This key will be deleted',
                    publicKey: 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... delete-key',
                    privateKeyEncrypted: 'encrypted-private-key',
                    encryptionIv: 'test-iv',
                    encryptionAuthTag: 'test-auth-tag',
                    fingerprint: 'bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99:aa',
                    keySize: 4096,
                    createdBy: testUser.id
                });
                testKeyId = sshKey.keyId;
            });

            it('should revoke SSH key', async () => {
                const response = await request(app)
                    .delete(`/api/security/keys/${testKeyId}`)
                    .set('Authorization', `Bearer ${authToken}`)
                    .send({
                        reason: 'Test revocation'
                    })
                    .expect(200);

                expect(response.body.message).toBe('SSH key revoked successfully');

                // Verify key is revoked
                const revokedKey = await SSHKey.findOne({ where: { keyId: testKeyId } });
                expect(revokedKey.isActive).toBe(false);
                expect(revokedKey.revokedAt).toBeDefined();
                expect(revokedKey.revocationReason).toBe('Test revocation');
            });

            it('should reject invalid key ID format', async () => {
                await request(app)
                    .delete('/api/security/keys/invalid-uuid')
                    .set('Authorization', `Bearer ${authToken}`)
                    .expect(400);
            });
        });
    });

    describe('TLS Certificate Management', () => {
        describe('POST /api/security/certs/generate', () => {
            it('should generate TLS certificate with valid data', async () => {
                const response = await request(app)
                    .post('/api/security/certs/generate')
                    .set('Authorization', `Bearer ${authToken}`)
                    .send({
                        name: 'Test TLS Certificate',
                        commonName: 'test.example.com',
                        organization: 'Test Organization',
                        validityDays: 365
                    })
                    .expect(201);

                expect(response.body.message).toBe('TLS certificate generated successfully');
                expect(response.body.certificate).toBeDefined();
                expect(response.body.certificate.certificateId).toBeDefined();
                expect(response.body.certificate.name).toBe('Test TLS Certificate');
                expect(response.body.certificate.certificate).toMatch(/^-----BEGIN CERTIFICATE-----/);
                expect(response.body.certificate.fingerprint).toBeDefined();
            });

            it('should reject missing common name', async () => {
                const response = await request(app)
                    .post('/api/security/certs/generate')
                    .set('Authorization', `Bearer ${authToken}`)
                    .send({
                        name: 'Test Certificate'
                        // Missing commonName
                    })
                    .expect(400);

                expect(response.body.error).toBe('Validation failed');
            });
        });

        describe('GET /api/security/certs', () => {
            beforeAll(async () => {
                // Create test TLS certificate
                await TLSCertificate.create({
                    certificateId: 'test-cert-id-1',
                    name: 'Test Certificate 1',
                    certificate: '-----BEGIN CERTIFICATE-----\ntest-cert-data\n-----END CERTIFICATE-----',
                    privateKeyEncrypted: 'encrypted-private-key',
                    publicKey: '-----BEGIN PUBLIC KEY-----\ntest-public-key\n-----END PUBLIC KEY-----',
                    fingerprint: 'AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD',
                    serialNumber: 'test-serial',
                    subject: 'CN=test.example.com,O=Test Org',
                    issuer: 'CN=test.example.com,O=Test Org',
                    validFrom: new Date(),
                    validTo: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000),
                    createdBy: testUser.id
                });
            });

            it('should list TLS certificates for authenticated user', async () => {
                const response = await request(app)
                    .get('/api/security/certs')
                    .set('Authorization', `Bearer ${authToken}`)
                    .expect(200);

                expect(response.body.certificates).toBeDefined();
                expect(Array.isArray(response.body.certificates)).toBe(true);
                expect(response.body.pagination).toBeDefined();
                expect(response.body.pagination.total).toBeGreaterThan(0);
            });
        });
    });
});