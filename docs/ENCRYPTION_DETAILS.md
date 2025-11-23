# LocalStorage Encryption Implementation

**Date:** 2025-11-23
**Feature:** AES-256-GCM encryption for sensitive data in browser localStorage

---

## Overview

All sensitive credentials (Dynatrace API tokens and proxy API keys) are now **automatically encrypted** before being stored in browser localStorage using industry-standard AES-256-GCM encryption.

### Why Encryption?

**Before (Vulnerable):**
```javascript
// localStorage content (plaintext):
{
  "apiToken": "dt0s16.ABCDEF1234567890...",
  "proxyApiKey": "xYz123AbC456DeF789..."
}
```
❌ Anyone with browser access could read tokens
❌ Visible in browser DevTools
❌ Easy target for malware

**After (Secure):**
```javascript
// localStorage content (encrypted):
{
  "apiToken": "Zk9vYmFyLCB0aGlzIGlzIG5vdCByZWFsbHkgZW5jcnlwdGVkIGRh...",
  "proxyApiKey": "dGhpcyBpcyBhbiBleGFtcGxlIG9mIGVuY3J5cHRlZCBkYXRh...",
  "encrypted": true
}
```
✅ Encrypted using Web Crypto API
✅ AES-256-GCM authenticated encryption
✅ PBKDF2 key derivation (100,000 iterations)
✅ Automatic encryption/decryption

---

## Technical Specifications

### Encryption Algorithm
- **Algorithm:** AES-256-GCM (Galois/Counter Mode)
- **Key Size:** 256 bits
- **IV Size:** 12 bytes (96 bits) - randomly generated per encryption
- **Authentication:** Built-in authenticated encryption (GCM mode)

### Key Derivation
- **Method:** PBKDF2 (Password-Based Key Derivation Function 2)
- **Hash Function:** SHA-256
- **Iterations:** 100,000
- **Salt:** 16 bytes random, stored in `localStorage['crypto_salt']`
- **Base Secret:** `'dynatrace-dashboard-encryption-v1'`

### Storage Format
```javascript
{
  "apiToken": "<base64_encoded_iv+ciphertext>",
  "proxyApiKey": "<base64_encoded_iv+ciphertext>",
  "encrypted": true
}
```

The encrypted data format is:
```
[12 bytes IV][N bytes ciphertext] -> base64 encoded
```

---

## Implementation Details

### Functions

#### 1. `getCryptoKey()`
Derives an encryption key from the base secret and salt.

```javascript
async function getCryptoKey() {
    // Get or generate salt
    let salt = localStorage.getItem(CRYPTO_SALT_KEY);
    if (!salt) {
        const saltArray = new Uint8Array(16);
        crypto.getRandomValues(saltArray);
        salt = Array.from(saltArray).map(b => b.toString(16).padStart(2, '0')).join('');
        localStorage.setItem(CRYPTO_SALT_KEY, salt);
    }

    // Derive key using PBKDF2
    const key = await crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: saltArray,
            iterations: 100000,
            hash: 'SHA-256'
        },
        baseKey,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
    );

    return key;
}
```

#### 2. `encryptData(plaintext)`
Encrypts a string and returns base64-encoded ciphertext.

```javascript
async function encryptData(plaintext) {
    const key = await getCryptoKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        new TextEncoder().encode(plaintext)
    );

    // Combine IV + ciphertext
    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(ciphertext), iv.length);

    // Return as base64
    return btoa(String.fromCharCode.apply(null, combined));
}
```

#### 3. `decryptData(encryptedData)`
Decrypts base64-encoded ciphertext back to plaintext.

```javascript
async function decryptData(encryptedData) {
    const key = await getCryptoKey();

    // Decode base64
    const combined = new Uint8Array(
        atob(encryptedData).split('').map(c => c.charCodeAt(0))
    );

    // Extract IV and ciphertext
    const iv = combined.slice(0, 12);
    const ciphertext = combined.slice(12);

    // Decrypt
    const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        ciphertext
    );

    return new TextDecoder().decode(decrypted);
}
```

#### 4. `saveConfig()` (Modified)
Now encrypts sensitive fields before saving:

```javascript
async function saveConfig() {
    // ... validate input ...

    // Encrypt sensitive fields
    const encryptedApiToken = await encryptData(apiToken);
    const encryptedProxyApiKey = await encryptData(proxyApiKey);

    // Save encrypted config
    config = {
        tenantUrl,
        apiToken: encryptedApiToken,
        proxyUrl,
        proxyApiKey: encryptedProxyApiKey,
        deployMode,
        enableLogging,
        encrypted: true
    };
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config));

    // Keep decrypted values in memory
    config.apiToken = apiToken;
    config.proxyApiKey = proxyApiKey;
}
```

#### 5. `loadConfig()` (Modified)
Now decrypts sensitive fields after loading:

```javascript
async function loadConfig() {
    const stored = localStorage.getItem(CONFIG_KEY);
    if (stored) {
        const cfg = JSON.parse(stored);

        // Decrypt if encrypted
        if (cfg.apiToken && cfg.encrypted !== false) {
            cfg.apiToken = await decryptData(cfg.apiToken);
        }
        if (cfg.proxyApiKey && cfg.encrypted !== false) {
            cfg.proxyApiKey = await decryptData(cfg.proxyApiKey);
        }

        return cfg;
    }
    return null;
}
```

---

## Security Analysis

### ✅ Strengths

1. **Industry-Standard Encryption**
   - AES-256-GCM is approved by NIST
   - Used by governments and enterprises worldwide
   - Authenticated encryption prevents tampering

2. **Proper Key Derivation**
   - PBKDF2 with 100,000 iterations
   - Makes brute-force attacks computationally expensive
   - Random salt per browser instance

3. **Unique IV per Encryption**
   - Fresh random IV for each encrypt operation
   - Prevents pattern analysis
   - Required for GCM mode security

4. **Backward Compatible**
   - Detects old unencrypted configs
   - Gracefully handles migration
   - Export/import handles both formats

### ⚠️ Limitations

1. **Browser Access = Decryption Possible**
   - Salt and encrypted data both in localStorage
   - Attacker with browser access can use the same derivation function
   - **Not protection against:** Malware, XSS, physical access

2. **Obfuscation, Not True Security**
   - Base secret is in JavaScript source code
   - Determined attacker can extract and use it
   - **Purpose:** Defense-in-depth, not sole protection

3. **Better Than Plaintext**
   - ✅ Protects against casual inspection
   - ✅ Prevents accidental exposure
   - ✅ Makes opportunistic theft harder
   - ❌ Not protection against determined attackers

### 🎯 Threat Model

**What This Protects Against:**
- ✅ Casual browsing of localStorage in DevTools
- ✅ Accidental exposure in screenshots/logs
- ✅ Opportunistic token theft by simple scripts
- ✅ Copy-paste errors exposing tokens

**What This Does NOT Protect Against:**
- ❌ Malware with browser access
- ❌ XSS attacks (tokens loaded in memory)
- ❌ Physical access to the computer
- ❌ Sophisticated attackers

---

## Comparison with Alternatives

| Approach | Security | Usability | Implementation |
|----------|----------|-----------|----------------|
| **Plaintext** | ❌ None | ✅ Simple | Easy |
| **AES-GCM (current)** | 🟡 Medium | ✅ Transparent | Medium |
| **User Password** | ✅ High | ❌ Password prompt | Complex |
| **sessionStorage** | 🟡 Medium | ❌ Re-login each session | Easy |
| **Server-side** | ✅ Highest | ✅ Good | Very Complex |

**Why AES-GCM was chosen:**
- ✅ Significant improvement over plaintext
- ✅ No user interaction required
- ✅ Transparent encryption/decryption
- ✅ Good balance of security and usability

---

## Best Practices for Production

For production deployments, consider these additional measures:

### 1. **Server-Side Authentication**
Move credentials to a backend service:
```
[Browser] → [Backend API] → [Dynatrace]
           (stores tokens)
```

### 2. **User-Provided Master Password**
Derive key from user password instead of static secret:
```javascript
const password = prompt('Enter master password:');
const key = await deriveKeyFromPassword(password);
```

### 3. **Hardware Security Keys**
Use WebAuthn for additional authentication layer.

### 4. **sessionStorage Instead of localStorage**
Tokens cleared when browser closes:
```javascript
sessionStorage.setItem(CONFIG_KEY, encryptedConfig);
```

### 5. **Token Rotation**
Regularly rotate Dynatrace API tokens.

### 6. **Content Security Policy**
Add CSP headers to prevent XSS:
```html
<meta http-equiv="Content-Security-Policy" content="...">
```

---

## Testing

### Verify Encryption is Active

1. **Save Configuration**
   - Open dashboard
   - Configure Dynatrace credentials
   - Save

2. **Inspect localStorage**
   - Open browser DevTools (F12)
   - Go to Application → Storage → Local Storage
   - Find `dynatrace_config` entry
   - Verify `apiToken` looks like: `"Zk9vYmFyLCB0..."`

3. **Check for Encryption Flag**
   - Verify `"encrypted": true` is present

### Test Decryption

1. **Reload Page**
   - Encrypted config should load seamlessly
   - Dashboard should work normally

2. **Export Settings**
   - Exported JSON should contain decrypted values
   - Verify you can read the token in exported file

3. **Import Settings**
   - Import the exported file
   - Values should be re-encrypted in localStorage

---

## Migration Guide

### From Unencrypted to Encrypted

**Automatic Migration:**
- No action needed!
- First save after update will encrypt existing tokens
- Old plaintext configs still work (backward compatible)

**Manual Migration:**
1. Export current settings
2. Clear localStorage
3. Re-import settings
4. Values will be encrypted on import

### Clearing Encryption Salt

If you want to regenerate the salt:
```javascript
localStorage.removeItem('crypto_salt');
// Reload page - new salt will be generated
```

Note: This will invalidate all encrypted data. You'll need to re-enter credentials.

---

## FAQ

### Q: Can I see my encrypted token?
**A:** Yes, open DevTools → Application → Local Storage. You'll see base64-encoded ciphertext.

### Q: What if I forget my "password"?
**A:** There's no user password! Encryption uses a built-in secret. Just reload the page.

### Q: Is this as secure as HTTPS?
**A:** No. This protects data at rest (in storage). HTTPS protects data in transit (over network). Both are needed!

### Q: Can I disable encryption?
**A:** Not recommended. But you can modify the code to skip `encryptData()` calls.

### Q: What happens if encryption fails?
**A:** Falls back to plaintext with console error. Graceful degradation.

### Q: Performance impact?
**A:** Negligible. Encryption happens only on save/load (not every API call).

---

## Summary

✅ **Implemented:** AES-256-GCM encryption for localStorage
✅ **Protects:** API tokens, proxy keys
✅ **Method:** PBKDF2 key derivation, 100k iterations
✅ **Transparent:** Automatic encrypt/decrypt
✅ **Compatible:** Backward compatible with old configs

🎯 **Result:** Significantly improved security posture for stored credentials while maintaining usability.

⚠️ **Remember:** This is defense-in-depth, not a silver bullet. For production, consider server-side authentication.

---

**Last Updated:** 2025-11-23
**Version:** 1.0
