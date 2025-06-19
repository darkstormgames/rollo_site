const crypto = require('crypto');
const forge = require('node-forge');
const { Client } = require('ssh2');
const SecurityUtils = require('./security');

class SSHKeyManager {
    static KEY_SIZE = 4096;
    static ENCRYPTION_ALGORITHM = 'aes-256-gcm';

    /**
     * Generate RSA SSH key pair (4096-bit)
     */
    static generateKeyPair() {
        const keyPair = forge.pki.rsa.generateKeyPair(this.KEY_SIZE);
        
        // Convert to PEM format
        const privateKeyPem = forge.pki.privateKeyToPem(keyPair.privateKey);
        const publicKeyPem = forge.pki.publicKeyToPem(keyPair.publicKey);
        
        // Convert public key to SSH format
        const publicKeySSH = this._convertToSSHPublicKey(keyPair.publicKey);
        
        return {
            keyId: SecurityUtils.generateKeyId(),
            privateKey: privateKeyPem,
            publicKey: publicKeySSH,
            fingerprint: this._generateFingerprint(publicKeySSH),
            createdAt: new Date().toISOString()
        };
    }

    /**
     * Encrypt private key for secure storage
     */
    static encryptPrivateKey(privateKey, encryptionKey) {
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipher(this.ENCRYPTION_ALGORITHM, encryptionKey);
        
        let encrypted = cipher.update(privateKey, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        
        const authTag = cipher.getAuthTag();
        
        return {
            encrypted,
            iv: iv.toString('hex'),
            authTag: authTag.toString('hex')
        };
    }

    /**
     * Decrypt private key from storage
     */
    static decryptPrivateKey(encryptedData, encryptionKey) {
        const decipher = crypto.createDecipher(
            this.ENCRYPTION_ALGORITHM, 
            encryptionKey
        );
        
        decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
        
        let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        
        return decrypted;
    }

    /**
     * Deploy SSH public key to remote server
     */
    static async deployKey(hostConfig, publicKey) {
        return new Promise((resolve, reject) => {
            const conn = new Client();
            
            conn.on('ready', () => {
                // Create .ssh directory and authorized_keys if they don't exist
                const setupCommand = `mkdir -p ~/.ssh && chmod 700 ~/.ssh`;
                const deployCommand = `echo "${publicKey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys`;
                
                conn.exec(setupCommand, (err, stream) => {
                    if (err) {
                        conn.end();
                        return reject(err);
                    }
                    
                    stream.on('close', (code) => {
                        if (code !== 0) {
                            conn.end();
                            return reject(new Error(`Setup failed with code ${code}`));
                        }
                        
                        // Now deploy the key
                        conn.exec(deployCommand, (err, stream) => {
                            if (err) {
                                conn.end();
                                return reject(err);
                            }
                            
                            stream.on('close', (code) => {
                                conn.end();
                                if (code === 0) {
                                    resolve({ success: true, message: 'Key deployed successfully' });
                                } else {
                                    reject(new Error(`Deployment failed with code ${code}`));
                                }
                            });
                        });
                    });
                });
            });
            
            conn.on('error', reject);
            
            // Set connection timeout
            const timeout = setTimeout(() => {
                conn.end();
                reject(new Error('Connection timeout'));
            }, 30000);
            
            conn.connect({
                host: hostConfig.host,
                port: hostConfig.port || 22,
                username: hostConfig.username,
                password: hostConfig.password || undefined,
                privateKey: hostConfig.privateKey || undefined,
                readyTimeout: 30000
            });
            
            conn.on('ready', () => clearTimeout(timeout));
        });
    }

    /**
     * Test SSH connection with key
     */
    static async testConnection(hostConfig, privateKey) {
        return new Promise((resolve, reject) => {
            const conn = new Client();
            
            conn.on('ready', () => {
                conn.exec('echo "Connection successful"', (err, stream) => {
                    if (err) {
                        conn.end();
                        return reject(err);
                    }
                    
                    stream.on('close', () => {
                        conn.end();
                        resolve({ success: true, message: 'Connection successful' });
                    });
                });
            });
            
            conn.on('error', reject);
            
            const timeout = setTimeout(() => {
                conn.end();
                reject(new Error('Connection timeout'));
            }, 30000);
            
            conn.connect({
                host: hostConfig.host,
                port: hostConfig.port || 22,
                username: hostConfig.username,
                privateKey: privateKey,
                readyTimeout: 30000
            });
            
            conn.on('ready', () => clearTimeout(timeout));
        });
    }

    /**
     * Convert forge public key to SSH format
     */
    static _convertToSSHPublicKey(publicKey) {
        // Extract public key components
        const n = publicKey.n;
        const e = publicKey.e;
        
        // Convert to SSH wire format
        const nBytes = this._mpintToBytes(n);
        const eBytes = this._mpintToBytes(e);
        
        // Build SSH public key format
        const keyType = 'ssh-rsa';
        const keyTypeBuffer = Buffer.from(keyType);
        
        const keyData = Buffer.concat([
            this._uint32ToBuffer(keyType.length),
            keyTypeBuffer,
            this._uint32ToBuffer(eBytes.length),
            eBytes,
            this._uint32ToBuffer(nBytes.length),
            nBytes
        ]);
        
        return `ssh-rsa ${keyData.toString('base64')} rollo-generated`;
    }

    /**
     * Convert forge BigInteger to bytes
     */
    static _mpintToBytes(bigInt) {
        const hex = bigInt.toString(16);
        const paddedHex = hex.length % 2 ? '0' + hex : hex;
        const buffer = Buffer.from(paddedHex, 'hex');
        
        // Add leading zero if first bit is set (for positive integers)
        if (buffer[0] & 0x80) {
            return Buffer.concat([Buffer.from([0x00]), buffer]);
        }
        
        return buffer;
    }

    /**
     * Convert uint32 to buffer
     */
    static _uint32ToBuffer(value) {
        const buffer = Buffer.allocUnsafe(4);
        buffer.writeUInt32BE(value, 0);
        return buffer;
    }

    /**
     * Generate fingerprint for SSH key
     */
    static _generateFingerprint(publicKey) {
        const keyData = publicKey.split(' ')[1];
        const keyBuffer = Buffer.from(keyData, 'base64');
        const hash = crypto.createHash('md5').update(keyBuffer).digest('hex');
        
        return hash.match(/.{2}/g).join(':');
    }

    /**
     * Validate SSH key format
     */
    static validateKeyFormat(key) {
        const sshKeyRegex = /^ssh-rsa\s+[A-Za-z0-9+/]+=*\s*.*/;
        return sshKeyRegex.test(key);
    }

    /**
     * Generate encryption key for key storage
     */
    static generateEncryptionKey() {
        return SecurityUtils.generateSecureRandom(32);
    }

    /**
     * Check if key needs rotation (older than 90 days)
     */
    static needsRotation(createdAt) {
        const created = new Date(createdAt);
        const now = new Date();
        const daysDiff = (now - created) / (1000 * 60 * 60 * 24);
        
        return daysDiff >= 90;
    }
}

module.exports = SSHKeyManager;