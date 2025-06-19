const crypto = require('crypto');
const forge = require('node-forge');
const SecurityUtils = require('./security');

class TLSCertificateManager {
    static KEY_SIZE = 2048;
    static DEFAULT_VALIDITY_DAYS = 365;

    /**
     * Generate TLS certificate and private key
     */
    static generateCertificate(options = {}) {
        const keyPair = forge.pki.rsa.generateKeyPair(this.KEY_SIZE);
        const cert = forge.pki.createCertificate();

        cert.publicKey = keyPair.publicKey;
        cert.serialNumber = SecurityUtils.generateSecureRandom(8);
        cert.validity.notBefore = new Date();
        cert.validity.notAfter = new Date();
        cert.validity.notAfter.setDate(
            cert.validity.notBefore.getDate() + (options.validityDays || this.DEFAULT_VALIDITY_DAYS)
        );

        const attrs = [
            { name: 'commonName', value: options.commonName || 'localhost' },
            { name: 'organizationName', value: options.organization || 'Rollo Games' },
            { name: 'organizationalUnitName', value: options.organizationalUnit || 'IT' },
            { name: 'countryName', value: options.country || 'US' },
            { name: 'stateOrProvinceName', value: options.state || 'State' },
            { name: 'localityName', value: options.locality || 'City' }
        ];

        cert.setSubject(attrs);
        cert.setIssuer(attrs);

        // Add extensions
        cert.setExtensions([
            {
                name: 'basicConstraints',
                cA: false
            },
            {
                name: 'keyUsage',
                keyCertSign: false,
                digitalSignature: true,
                nonRepudiation: true,
                keyEncipherment: true,
                dataEncipherment: true
            },
            {
                name: 'extKeyUsage',
                serverAuth: true,
                clientAuth: true
            },
            {
                name: 'subjectAltName',
                altNames: options.altNames || [
                    { type: 2, value: 'localhost' },
                    { type: 7, ip: '127.0.0.1' }
                ]
            }
        ]);

        // Self-sign the certificate
        cert.sign(keyPair.privateKey, forge.md.sha256.create());

        return {
            certificateId: SecurityUtils.generateKeyId(),
            certificate: forge.pki.certificateToPem(cert),
            privateKey: forge.pki.privateKeyToPem(keyPair.privateKey),
            publicKey: forge.pki.publicKeyToPem(keyPair.publicKey),
            fingerprint: this._generateCertificateFingerprint(cert),
            serialNumber: cert.serialNumber,
            validFrom: cert.validity.notBefore.toISOString(),
            validTo: cert.validity.notAfter.toISOString(),
            subject: this._getSubjectString(cert.subject),
            createdAt: new Date().toISOString()
        };
    }

    /**
     * Generate Certificate Authority (CA)
     */
    static generateCA(options = {}) {
        const keyPair = forge.pki.rsa.generateKeyPair(this.KEY_SIZE);
        const cert = forge.pki.createCertificate();

        cert.publicKey = keyPair.publicKey;
        cert.serialNumber = '01';
        cert.validity.notBefore = new Date();
        cert.validity.notAfter = new Date();
        cert.validity.notAfter.setFullYear(
            cert.validity.notBefore.getFullYear() + (options.validityYears || 10)
        );

        const attrs = [
            { name: 'commonName', value: options.commonName || 'Rollo Games CA' },
            { name: 'organizationName', value: options.organization || 'Rollo Games' },
            { name: 'organizationalUnitName', value: options.organizationalUnit || 'Certificate Authority' },
            { name: 'countryName', value: options.country || 'US' }
        ];

        cert.setSubject(attrs);
        cert.setIssuer(attrs);

        cert.setExtensions([
            {
                name: 'basicConstraints',
                cA: true,
                pathLenConstraint: 0
            },
            {
                name: 'keyUsage',
                keyCertSign: true,
                cRLSign: true
            }
        ]);

        cert.sign(keyPair.privateKey, forge.md.sha256.create());

        return {
            certificateId: SecurityUtils.generateKeyId(),
            certificate: forge.pki.certificateToPem(cert),
            privateKey: forge.pki.privateKeyToPem(keyPair.privateKey),
            publicKey: forge.pki.publicKeyToPem(keyPair.publicKey),
            fingerprint: this._generateCertificateFingerprint(cert),
            isCA: true,
            createdAt: new Date().toISOString()
        };
    }

    /**
     * Sign certificate with CA
     */
    static signCertificate(csr, caPrivateKey, caCert, options = {}) {
        const cert = forge.pki.createCertificate();
        const csrObj = forge.pki.certificationRequestFromPem(csr);
        const caCertObj = forge.pki.certificateFromPem(caCert);

        cert.publicKey = csrObj.publicKey;
        cert.serialNumber = SecurityUtils.generateSecureRandom(8);
        cert.validity.notBefore = new Date();
        cert.validity.notAfter = new Date();
        cert.validity.notAfter.setDate(
            cert.validity.notBefore.getDate() + (options.validityDays || this.DEFAULT_VALIDITY_DAYS)
        );

        cert.setSubject(csrObj.subject.attributes);
        cert.setIssuer(caCertObj.subject.attributes);

        cert.setExtensions([
            {
                name: 'basicConstraints',
                cA: false
            },
            {
                name: 'keyUsage',
                digitalSignature: true,
                keyEncipherment: true
            },
            {
                name: 'extKeyUsage',
                serverAuth: true,
                clientAuth: true
            }
        ]);

        const caPrivateKeyObj = forge.pki.privateKeyFromPem(caPrivateKey);
        cert.sign(caPrivateKeyObj, forge.md.sha256.create());

        return {
            certificateId: SecurityUtils.generateKeyId(),
            certificate: forge.pki.certificateToPem(cert),
            fingerprint: this._generateCertificateFingerprint(cert),
            serialNumber: cert.serialNumber,
            validFrom: cert.validity.notBefore.toISOString(),
            validTo: cert.validity.notAfter.toISOString(),
            signedBy: this._generateCertificateFingerprint(caCertObj),
            createdAt: new Date().toISOString()
        };
    }

    /**
     * Validate certificate
     */
    static validateCertificate(certificatePem) {
        try {
            const cert = forge.pki.certificateFromPem(certificatePem);
            const now = new Date();
            
            return {
                valid: now >= cert.validity.notBefore && now <= cert.validity.notAfter,
                notBefore: cert.validity.notBefore,
                notAfter: cert.validity.notAfter,
                expired: now > cert.validity.notAfter,
                notYetValid: now < cert.validity.notBefore,
                fingerprint: this._generateCertificateFingerprint(cert),
                subject: this._getSubjectString(cert.subject),
                issuer: this._getSubjectString(cert.issuer)
            };
        } catch (error) {
            return {
                valid: false,
                error: error.message
            };
        }
    }

    /**
     * Check if certificate needs renewal (expires within 30 days)
     */
    static needsRenewal(certificatePem, renewalDays = 30) {
        try {
            const cert = forge.pki.certificateFromPem(certificatePem);
            const now = new Date();
            const renewalDate = new Date(cert.validity.notAfter);
            renewalDate.setDate(renewalDate.getDate() - renewalDays);
            
            return now >= renewalDate;
        } catch (error) {
            return true; // If we can't parse it, it needs renewal
        }
    }

    /**
     * Extract certificate information
     */
    static getCertificateInfo(certificatePem) {
        try {
            const cert = forge.pki.certificateFromPem(certificatePem);
            
            return {
                subject: this._getSubjectString(cert.subject),
                issuer: this._getSubjectString(cert.issuer),
                serialNumber: cert.serialNumber,
                validFrom: cert.validity.notBefore.toISOString(),
                validTo: cert.validity.notAfter.toISOString(),
                fingerprint: this._generateCertificateFingerprint(cert),
                keySize: cert.publicKey.n.bitLength(),
                algorithm: 'RSA',
                extensions: cert.extensions.map(ext => ({
                    name: ext.name,
                    critical: ext.critical
                }))
            };
        } catch (error) {
            throw new Error(`Failed to parse certificate: ${error.message}`);
        }
    }

    /**
     * Generate certificate fingerprint
     */
    static _generateCertificateFingerprint(cert) {
        const certDer = forge.asn1.toDer(forge.pki.certificateToAsn1(cert)).getBytes();
        const hash = forge.md.sha256.create();
        hash.update(certDer);
        return hash.digest().toHex().match(/.{2}/g).join(':').toUpperCase();
    }

    /**
     * Get subject string from certificate
     */
    static _getSubjectString(subject) {
        return subject.attributes.map(attr => 
            `${attr.shortName || attr.name}=${attr.value}`
        ).join(', ');
    }

    /**
     * Encrypt certificate private key
     */
    static encryptPrivateKey(privateKey, password) {
        const encryptedPem = forge.pki.encryptRsaPrivateKey(
            forge.pki.privateKeyFromPem(privateKey),
            password,
            { algorithm: 'aes256' }
        );
        
        return encryptedPem;
    }

    /**
     * Decrypt certificate private key
     */
    static decryptPrivateKey(encryptedPrivateKey, password) {
        const privateKey = forge.pki.decryptRsaPrivateKey(encryptedPrivateKey, password);
        return forge.pki.privateKeyToPem(privateKey);
    }
}

module.exports = TLSCertificateManager;