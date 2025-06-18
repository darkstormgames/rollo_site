const request = require('supertest');
const app = require('../server');
const db = require('../src/config/database');

describe('Auth API', () => {
    let testUser = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'TestPass123!',
        firstName: 'Test',
        lastName: 'User'
    };

    afterAll(async () => {
        // Clean up test data
        await db.query('DELETE FROM users WHERE email = ?', [testUser.email]);
        await db.close();
    });

    describe('POST /api/auth/register', () => {
        it('should register a new user with valid data', async () => {
            const response = await request(app)
                .post('/api/auth/register')
                .send(testUser)
                .expect(201);

            expect(response.body.message).toBe('User registered successfully');
            expect(response.body.user.username).toBe(testUser.username);
            expect(response.body.user.email).toBe(testUser.email);
            expect(response.body.user.password_hash).toBeUndefined();
        });

        it('should reject duplicate username', async () => {
            await request(app)
                .post('/api/auth/register')
                .send(testUser)
                .expect(409);
        });

        it('should reject weak password', async () => {
            const weakUser = { ...testUser, username: 'weakpass', email: 'weak@example.com', password: '123' };
            const response = await request(app)
                .post('/api/auth/register')
                .send(weakUser)
                .expect(400);

            expect(response.body.error).toBe('Validation failed');
        });
    });

    describe('POST /api/auth/login', () => {
        it('should login with valid credentials', async () => {
            const response = await request(app)
                .post('/api/auth/login')
                .send({
                    username: testUser.username,
                    password: testUser.password
                })
                .expect(200);

            expect(response.body.message).toBe('Login successful');
            expect(response.body.accessToken).toBeDefined();
            expect(response.body.refreshToken).toBeDefined();
            expect(response.body.user.username).toBe(testUser.username);
        });

        it('should reject invalid credentials', async () => {
            await request(app)
                .post('/api/auth/login')
                .send({
                    username: testUser.username,
                    password: 'wrongpassword'
                })
                .expect(401);
        });
    });

    describe('POST /api/auth/refresh', () => {
        let refreshToken;

        beforeAll(async () => {
            const loginResponse = await request(app)
                .post('/api/auth/login')
                .send({
                    username: testUser.username,
                    password: testUser.password
                });
            
            refreshToken = loginResponse.body.refreshToken;
        });

        it('should refresh access token with valid refresh token', async () => {
            const response = await request(app)
                .post('/api/auth/refresh')
                .send({ refreshToken })
                .expect(200);

            expect(response.body.message).toBe('Token refreshed successfully');
            expect(response.body.accessToken).toBeDefined();
        });

        it('should reject invalid refresh token', async () => {
            await request(app)
                .post('/api/auth/refresh')
                .send({ refreshToken: 'invalid-token' })
                .expect(403);
        });
    });

    describe('POST /api/auth/logout', () => {
        it('should logout successfully', async () => {
            const response = await request(app)
                .post('/api/auth/logout')
                .send({ refreshToken: 'some-token' })
                .expect(200);

            expect(response.body.message).toBe('Logout successful');
        });
    });
});