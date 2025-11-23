# CLAUDE.md - AI Assistant Guide

This document provides comprehensive guidance for AI assistants working with the Single-Use Dashboard codebase. It covers the architecture, conventions, workflows, and key considerations for making effective contributions.

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Architecture](#codebase-architecture)
3. [Technology Stack](#technology-stack)
4. [Key Files and Locations](#key-files-and-locations)
5. [Development Workflows](#development-workflows)
6. [Code Conventions](#code-conventions)
7. [Security Considerations](#security-considerations)
8. [Testing and Validation](#testing-and-validation)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## Repository Overview

### Project Type
**Single-Page Application (SPA) Dashboard** - A lightweight web-based analytics dashboard for visualizing Dynatrace data through DQL (Dynatrace Query Language) queries.

### Project Structure
```
singleuse-dashboard/
├── README.md                          # User-facing documentation
├── CLAUDE.md                          # This file - AI assistant guide
├── LICENSE                            # MIT License
├── src/                               # Source code
│   ├── dashboard.html                # Main SPA (2,506 lines)
│   ├── proxy_server.py               # Python proxy backend (392 lines)
│   └── proxy.php                     # PHP proxy alternative (228 lines)
├── docs/                              # Security documentation
│   ├── SECURITY_REPORT.md            # Security audit findings
│   ├── SECURITY_FIXES_SUMMARY.md     # Implementation details
│   └── ENCRYPTION_DETAILS.md         # Encryption specifications
└── assets/                            # Media files
    └── dashboard-sshot01.png         # Screenshot
```

### Key Characteristics
- **No build step required** - Direct HTML/CSS/JavaScript deployment
- **No external dependencies** - Uses only standard JavaScript Web APIs
- **Dual proxy system** - Python (local dev) or PHP (production webserver)
- **Security-hardened** - 8/9 vulnerabilities fixed, comprehensive encryption
- **Browser-based storage** - All configuration stored in localStorage (encrypted)

---

## Codebase Architecture

### Application Layers

#### 1. Frontend Layer (dashboard.html)
The entire frontend is contained in a single HTML file with three main sections:

**HTML Structure** (Lines 1-200)
- Minimal markup: header, tile grid, events table, modals
- All content dynamically generated via JavaScript
- No server-side rendering

**CSS Styles** (Lines 201-964)
- Responsive hexagonal tile layout
- Modal dialog styling
- Dark-friendly color scheme
- SVG hexagon rendering

**JavaScript Application** (Lines 965-2506)
- Functional organization (no frameworks)
- Encryption utilities
- Configuration management
- Tile and table rendering
- DQL query execution
- Real-time data visualization

#### 2. Backend Layer (Proxy Servers)

**Python Proxy (proxy_server.py)**
- HTTP server using `http.server.BaseHTTPRequestHandler`
- API key authentication with constant-time comparison
- CORS handling with whitelist-based origin validation
- SSRF protection with domain/IP validation
- Serves both the dashboard and proxies Dynatrace API calls

**PHP Proxy (proxy.php)**
- cURL-based HTTP client
- Rate limiting (30 requests/minute per IP)
- API key authentication
- Similar SSRF protections

### Data Flow

```
User Browser
    ↓ (encrypted localStorage)
Dashboard UI
    ↓ (DQL queries + credentials)
Proxy Server (Python/PHP)
    ↓ (authenticated API calls)
Dynatrace API
    ↓ (query results)
Proxy Server
    ↓ (JSON response)
Dashboard UI
    ↓ (render hexagons/tables)
User Browser
```

### State Management

**Global State Keys:**
```javascript
CONFIG_KEY = 'dynatrace_config'           // Encrypted credentials
PREFERENCES_KEY = 'dashboard_preferences'  // UI preferences
TILES_CONFIG_KEY = 'tiles_config'         // Tile configurations
VARIABLES_KEY = 'global_variables'        // User-defined variables
TABLE_QUERY_KEY = 'custom_table_query'    // Custom DQL query
CRYPTO_SALT_KEY = 'crypto_salt'           // Encryption salt
```

**Data Structures:**
```javascript
// Configuration object
config = {
    tenantUrl: string,      // e.g., "https://xxx.apps.dynatrace.com"
    apiToken: string,       // Encrypted in storage
    proxyUrl: string,       // e.g., "http://localhost:8081"
    proxyApiKey: string,    // Encrypted in storage
    deployMode: "proxy" | "php-proxy",
    enableLogging: boolean,
    encrypted: boolean      // Migration flag
}

// Tile configuration
tile = {
    id: string,            // e.g., "tile1"
    title: string,         // Display title
    query: string,         // DQL query
    nameField: string,     // Result field for entity name
    statusField: string,   // Result field for status (OK/WARN/ALERT)
    linkField?: string     // Optional result field for link
}
```

---

## Technology Stack

### Frontend
- **Languages:** HTML5, CSS3, Vanilla JavaScript (ES6+)
- **APIs Used:**
  - Web Crypto API (AES-256-GCM encryption)
  - Fetch API (HTTP requests)
  - localStorage API (client-side storage)
  - SVG (hexagon rendering)
- **Security:** DOMPurify 3.0.6 (via CDN)
- **No framework dependencies** - Pure JavaScript

### Backend
- **Python:** 3.6+ (standard library only)
  - `http.server` for HTTP handling
  - `urllib` for proxying
  - `secrets` for API key generation
  - `hashlib` for token hashing
  - `ipaddress` for IP validation

- **PHP:** 7.0+ (cURL extension required)
  - Native cURL for HTTP requests
  - Built-in session handling

### External Services
- **Dynatrace API:** Platform/storage/query/v1 endpoint
- **Required Token Scopes:**
  - `storage:buckets:read`
  - `storage:events:read`
  - `storage:metrics:read`
  - `storage:logs:read`
  - `storage:entities:read`

---

## Key Files and Locations

### Source Code

| File | Lines | Purpose | Key Sections |
|------|-------|---------|--------------|
| **dashboard.html** | 2,506 | Main application | Encryption (965-1191), Config (1277-1550), Tiles (1939-2109), Table (2111-2280), DQL (2282-2412) |
| **proxy_server.py** | 392 | Python proxy | API key generation (46-68), SSRF validation (70-158), Request handling (160-390) |
| **proxy.php** | 228 | PHP proxy | Rate limiting (40-68), API proxying (85-195) |

### Documentation

| File | Purpose | When to Read |
|------|---------|--------------|
| **README.md** | User-facing setup guide | Understanding user workflows |
| **SECURITY_REPORT.md** | Audit findings and fixes | Before making security changes |
| **SECURITY_FIXES_SUMMARY.md** | Implementation details | Understanding security patterns |
| **ENCRYPTION_DETAILS.md** | Encryption specifications | Working with crypto code |

### Code Locations by Feature

**Encryption System** (dashboard.html:965-1191)
- `getCryptoKey(password, salt)` - PBKDF2 key derivation
- `encryptData(data, password)` - AES-256-GCM encryption
- `decryptData(encryptedData, password)` - Decryption with validation
- `migrateUnencryptedConfig()` - Auto-migration from plaintext

**Configuration Management** (dashboard.html:1277-1550)
- `loadConfig()` - Load and decrypt from localStorage
- `saveConfig()` - Encrypt and save to localStorage
- `exportSettings()` - Download JSON backup
- `importSettings()` - Upload JSON restore
- `showConfig()` - Configuration modal UI

**Timeframe & Variables** (dashboard.html:1562-1695)
- `getTimeframeForAPI()` - Convert UI selector to timestamps
- `replaceVariables(query)` - Substitute `${{VAR_NAME}}` syntax
- `getTimeframeVariables()` - Auto-variables (TIMEFRAME_START/END)

**Tile Management** (dashboard.html:1939-2109)
- `renderTiles()` - Create hexagonal tile UI
- `loadTileData(tile)` - Execute DQL and render hexagons
- `createHexagon(color)` - SVG hexagon creation
- `showTileConfig(tileId)` - Tile configuration modal

**Table Management** (dashboard.html:2111-2280)
- `sortTable(columnIndex)` - Client-side column sorting
- `renderTableData(records)` - Render table with formatting
- `loadEvents()` - Fetch and render events table

**DQL Execution** (dashboard.html:2282-2412)
- `executeDQL(query)` - Route to appropriate proxy
- `executeDQLProxy(query)` - Python proxy mode
- `executeDQLPHPProxy(query)` - PHP proxy mode
- `updateProxyStatus()` - Connection status indicator

**Security Utilities** (proxy_server.py:70-158)
- `is_valid_dynatrace_url(url)` - Domain whitelist validation
- `is_private_ip(ip)` - Private IP range detection
- `validate_tenant_url(url)` - Complete SSRF protection

---

## Development Workflows

### Local Development Setup

1. **Start Python Proxy:**
   ```bash
   python3 src/proxy_server.py
   # Server starts on http://localhost:8081
   # Copy the API key displayed in console
   ```

2. **Open Dashboard:**
   - Navigate to http://localhost:8081
   - Configure with proxy API key
   - Add Dynatrace credentials

3. **Development Cycle:**
   - Edit `src/dashboard.html`
   - Refresh browser (no build step)
   - Check browser console for errors

### Making Code Changes

#### When Modifying JavaScript

**DO:**
- Read the entire relevant section before editing
- Preserve existing encryption patterns
- Use `textContent` instead of `innerHTML` for user input
- Validate and sanitize all external data
- Test with browser DevTools console open
- Check for XSS vulnerabilities

**DON'T:**
- Remove or bypass security checks
- Store sensitive data in plaintext
- Use `innerHTML` with user-controlled content
- Skip error handling
- Add framework dependencies without discussion

#### When Modifying Proxy Servers

**DO:**
- Maintain SSRF protection checks
- Preserve API key authentication
- Keep CORS whitelist restrictions
- Use constant-time comparison for secrets
- Log errors server-side only (generic messages to client)

**DON'T:**
- Disable security validations
- Log sensitive tokens or keys
- Allow wildcard CORS origins
- Expose internal error details to clients

### Testing Changes

**Manual Testing Checklist:**
1. Configuration save/load works
2. Encryption/decryption functions correctly
3. Export/import preserves settings
4. Tiles load and display data
5. Events table sorts correctly
6. Variable substitution works in queries
7. Auto-refresh triggers on schedule
8. Proxy connection indicator accurate

**Security Testing:**
1. Check DevTools → Application → localStorage (values should be encrypted)
2. Try invalid URLs (should be rejected)
3. Test XSS payloads in inputs (should be sanitized)
4. Verify API key requirement (requests without key should fail)

**Browser Console Checks:**
```javascript
// Verify encryption is active
localStorage.getItem('dynatrace_config'); // Should show encrypted blob

// Test decryption (should work silently)
location.reload();

// Check for errors
// No red errors should appear in console
```

### Git Workflow

**Branch Naming Convention:**
- All development branches MUST start with `claude/`
- Format: `claude/[session-id]` (auto-generated)
- Example: `claude/claude-md-mic3k2c4hieg4lu8-01UV1sE7cuQQkTnVQQX43jeE`

**Commit Process:**
```bash
# Stage changes
git add src/dashboard.html

# Commit with descriptive message
git commit -m "Add feature X: Brief description of what changed"

# Push to Claude branch (with retry logic)
git push -u origin claude/[branch-name]
```

**Commit Message Guidelines:**
- Start with verb: "Add", "Fix", "Update", "Remove", "Refactor"
- Be specific about what changed
- Reference issue numbers if applicable
- Keep under 72 characters for first line

**Examples:**
- ✅ "Fix XSS vulnerability in table rendering"
- ✅ "Add rate limiting to Python proxy"
- ✅ "Update encryption to use 100k iterations"
- ❌ "Fixed stuff"
- ❌ "Changes"

---

## Code Conventions

### JavaScript Style

**Naming:**
```javascript
// camelCase for variables and functions
let proxyApiKey = '';
function loadTileData() { }

// UPPERCASE for constants
const CONFIG_KEY = 'dynatrace_config';
const REFRESH_INTERVAL = 30000;

// Descriptive names (avoid abbreviations)
const tenantUrl = '';  // ✅ Good
const tUrl = '';       // ❌ Avoid
```

**Function Organization:**
```javascript
// Async/await for async operations
async function encryptData(data, password) {
    const key = await getCryptoKey(password, salt);
    // ...
}

// Promise.all for parallel operations
async function loadAllTiles() {
    const promises = tiles.map(tile => loadTileData(tile));
    await Promise.all(promises);
}

// Try/catch for error handling
async function saveConfig() {
    try {
        const encrypted = await encryptData(config, password);
        localStorage.setItem(CONFIG_KEY, encrypted);
    } catch (error) {
        console.error('Failed to save config:', error);
        alert('Error saving configuration');
    }
}
```

**DOM Manipulation (Security-Critical):**
```javascript
// ✅ GOOD - Safe methods
element.textContent = userInput;
element.setAttribute('href', validatedUrl);
const div = document.createElement('div');

// ❌ BAD - Unsafe methods
element.innerHTML = userInput;  // XSS risk!
eval(userCode);                 // Code injection!
```

**Comment Style:**
```javascript
// Section headers (for major sections)
// ==================== ENCRYPTION UTILITIES ====================

// Function documentation (for complex functions)
/**
 * Encrypts data using AES-256-GCM with PBKDF2 key derivation
 * @param {Object} data - Data to encrypt
 * @param {string} password - User password
 * @returns {Promise<string>} Base64-encoded encrypted data
 */
async function encryptData(data, password) { }

// Inline comments (for complex logic)
// Generate random IV for this encryption operation
const iv = window.crypto.getRandomValues(new Uint8Array(12));
```

### Python Style (proxy_server.py)

**Naming:**
```python
# snake_case for functions and variables
def is_valid_dynatrace_url(url):
    pass

# UPPER_CASE for constants
ALLOWED_ORIGINS = [...]
DYNATRACE_DOMAINS = [...]
```

**Error Handling:**
```python
# Specific exceptions
try:
    response = urllib.request.urlopen(request)
except urllib.error.HTTPError as e:
    # Handle HTTP errors
    pass
except urllib.error.URLError as e:
    # Handle network errors
    pass
```

**Security Patterns:**
```python
# Constant-time comparison for secrets
import secrets
if secrets.compare_digest(provided_key, stored_key):
    # Authenticated
    pass

# Never log sensitive data
logging.info(f"Token hash: {hashlib.sha256(token.encode()).hexdigest()[:8]}")
```

### PHP Style (proxy.php)

**Security Patterns:**
```php
// Constant-time comparison
if (hash_equals($expected, $provided)) {
    // Authenticated
}

// Input validation
if (!filter_var($url, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    exit;
}
```

---

## Security Considerations

### Critical Security Rules

**NEVER:**
1. Store credentials in plaintext
2. Use `innerHTML` with user input
3. Bypass SSRF validation checks
4. Remove API key authentication
5. Log sensitive tokens or keys
6. Allow wildcard CORS origins
7. Expose internal error details to clients
8. Skip input validation

**ALWAYS:**
1. Encrypt sensitive data before localStorage
2. Validate and sanitize all user input
3. Use safe DOM APIs (`textContent`, `createElement`)
4. Check URLs against whitelist
5. Use constant-time comparison for secrets
6. Hash tokens in logs (SHA256)
7. Return generic error messages to clients
8. Test for XSS vulnerabilities

### Current Security Posture

**Status:** 8/9 vulnerabilities fixed (89%)

**Fixed Issues (P0 - Critical):**
- ✅ Insecure credential storage → AES-256-GCM encryption
- ✅ Cross-Site Scripting (XSS) → DOMPurify + safe DOM APIs
- ✅ Open CORS policy → Whitelist validation
- ✅ No proxy authentication → API key with constant-time check
- ✅ SSRF vulnerability → Domain/IP validation
- ✅ Information disclosure → Generic error messages
- ✅ Token in logs → SHA256 hashing

**Open Issues (Low Priority):**
- ⚠️ Path traversal (low risk - hardcoded paths)
- ⚠️ Rate limiting (partial - PHP only)

### Encryption Implementation

**Algorithm:** AES-256-GCM (Galois/Counter Mode)
**Key Derivation:** PBKDF2-SHA256, 100,000 iterations
**Storage Format:** Base64([12-byte IV] + [ciphertext])

**Key Functions:**
```javascript
// Key derivation (dashboard.html:972-993)
async function getCryptoKey(password, salt) {
    const keyMaterial = await window.crypto.subtle.importKey(/*...*/);
    return await window.crypto.subtle.deriveKey(
        { name: "PBKDF2", salt, iterations: 100000, hash: "SHA-256" },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["encrypt", "decrypt"]
    );
}

// Encryption (dashboard.html:995-1027)
async function encryptData(data, password) {
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await window.crypto.subtle.encrypt(
        { name: "AES-GCM", iv },
        key,
        encoder.encode(JSON.stringify(data))
    );
    return btoa(String.fromCharCode(...iv, ...new Uint8Array(encrypted)));
}
```

### XSS Protection Strategy

**Multiple Layers:**
1. **Input Sanitization:** DOMPurify for markdown content
2. **HTML Encoding:** Before any rendering
3. **Safe DOM APIs:** `textContent`, `createElement`, `setAttribute`
4. **URL Validation:** Full scheme and format checking
5. **Link Safety:** `noopener,noreferrer` flags

**Example (Secure Link Rendering):**
```javascript
// dashboard.html:2198-2222
if (isUrl && isValidUrl(cellData)) {
    const link = document.createElement('a');
    link.href = cellData;  // Already validated
    link.textContent = cellData;  // Safe text content
    link.target = '_blank';
    link.rel = 'noopener noreferrer';  // Security flags
    cell.appendChild(link);
}
```

### SSRF Protection

**Validation Rules (proxy_server.py:70-158):**
1. Parse and validate URL format
2. Check domain against whitelist:
   - `*.dynatrace.com`
   - `*.dynatracelabs.com`
   - `*.dynatrace-managed.com`
3. Resolve hostname to IP
4. Reject private IPs:
   - 10.0.0.0/8
   - 192.168.0.0/16
   - 172.16.0.0/12
5. Reject localhost/loopback
6. Reject cloud metadata (169.254.169.254)

---

## Testing and Validation

### No Formal Test Suite

This project has no automated testing infrastructure. All testing is manual.

### Manual Testing Procedures

**After Code Changes:**
1. **Visual Inspection:**
   - Load dashboard in browser
   - Check all tiles render correctly
   - Verify events table displays data
   - Test modal dialogs open/close

2. **Configuration Testing:**
   - Save configuration
   - Reload page (test decryption)
   - Export settings to JSON
   - Import settings from JSON
   - Verify all fields preserved

3. **Encryption Testing:**
   ```javascript
   // In browser console
   localStorage.getItem('dynatrace_config');
   // Should show encrypted blob like: "aBcDeFgHiJ..."
   // NOT plaintext like: {"tenantUrl":"..."}
   ```

4. **Security Testing:**
   ```javascript
   // Test XSS protection (should be sanitized)
   // Try entering in tile title: <script>alert('XSS')</script>

   // Test URL validation (should be rejected)
   // Try entering tenant URL: http://localhost

   // Test API key requirement (should fail with 401)
   // Remove X-API-Key header in DevTools Network tab
   ```

5. **Functionality Testing:**
   - Variable substitution: `${{VAR_NAME}}` in queries
   - Timeframe selector: Changes data range
   - Auto-refresh: Triggers at configured interval
   - Sorting: Click table headers
   - Links: Click links in table (opens new tab)

### Browser Console Monitoring

**Expected Output:**
```
✅ Config loaded successfully
✅ Proxy status: OK
✅ All tiles loaded
✅ Events table loaded
```

**Red Flags:**
```
❌ Uncaught TypeError: ...
❌ Failed to fetch
❌ 401 Unauthorized
❌ CORS error
```

### Validation Scripts

**Check Encryption Status:**
```javascript
// Run in browser console
const config = localStorage.getItem('dynatrace_config');
if (config && config.length > 100 && !config.includes('{')) {
    console.log('✅ Config is encrypted');
} else {
    console.log('❌ Config is NOT encrypted');
}
```

**Verify Token Not Logged:**
```bash
# Check Python proxy logs
grep -i "apitoken" proxy_logs.txt
# Should show: "Token hash: a1b2c3d4..."
# Should NOT show: "Bearer dt0..."
```

---

## Common Tasks

### Adding a New Feature

1. **Plan the implementation:**
   - Identify which file(s) need changes
   - Determine if security implications exist
   - Check if encryption needed for new data

2. **Locate the relevant code section:**
   - Use line numbers from "Key Files and Locations"
   - Read surrounding code for context
   - Understand existing patterns

3. **Implement the feature:**
   - Follow code conventions
   - Add error handling
   - Use safe DOM APIs
   - Test thoroughly

4. **Update documentation:**
   - Add comments for complex logic
   - Update README.md if user-facing
   - Note any security considerations

### Fixing a Bug

1. **Reproduce the issue:**
   - Load dashboard in browser
   - Open DevTools console
   - Trigger the bug
   - Note exact error message

2. **Locate the bug:**
   - Search for error message in dashboard.html
   - Check relevant code section
   - Add console.log statements if needed

3. **Fix the bug:**
   - Make minimal changes
   - Test the specific scenario
   - Ensure no regressions

4. **Verify the fix:**
   - Test original scenario
   - Test related scenarios
   - Check console for new errors

### Adding Security Improvements

1. **Review security documentation:**
   - Read docs/SECURITY_REPORT.md
   - Understand current protections
   - Identify gaps

2. **Implement the improvement:**
   - Follow existing security patterns
   - Add validation/sanitization
   - Test for bypasses

3. **Document the change:**
   - Update SECURITY_REPORT.md
   - Note in SECURITY_FIXES_SUMMARY.md
   - Add code comments

### Modifying DQL Queries

**Default Queries Location:**
- Tiles: Inline in dashboard.html (search for `query:`)
- Table: `loadEvents()` function (dashboard.html:2111)

**Variable Substitution:**
```javascript
// Syntax: ${{VARIABLE_NAME}}
query = "fetch events | filter region == '${{REGION}}'"

// Auto-variables (always available):
// ${{TIMEFRAME_START}} - Unix timestamp (ms)
// ${{TIMEFRAME_END}}   - Unix timestamp (ms)
query = "fetch logs, from: ${{TIMEFRAME_START}}, to: ${{TIMEFRAME_END}}"
```

### Updating Proxy Configuration

**Python Proxy (proxy_server.py):**
```python
# Port (line ~360)
PORT = 8081

# CORS origins (line ~25)
ALLOWED_ORIGINS = [
    'http://localhost:8081',
    'http://127.0.0.1:8081',
]

# Dynatrace domains (line ~70)
DYNATRACE_DOMAINS = [
    'dynatrace.com',
    'dynatracelabs.com',
    'dynatrace-managed.com',
]
```

**PHP Proxy (proxy.php):**
```php
// API key (line ~12)
define('PROXY_API_KEY', 'your-secret-key');

// Rate limit (line ~15)
define('RATE_LIMIT', 30); // requests per minute
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### "401 Unauthorized" from Proxy

**Cause:** Missing or invalid proxy API key

**Solution:**
1. Restart Python proxy to see key in console
2. Copy the key exactly (including all characters)
3. Paste into dashboard Config → Python Proxy API Key
4. Save configuration

**Verification:**
```bash
# Python proxy console should show:
✅ API key validated successfully

# Dashboard console should show:
✅ Proxy status: OK
```

#### "401 Unauthorized" from Dynatrace

**Cause:** Invalid or expired Dynatrace API token

**Solution:**
1. Log into Dynatrace
2. Navigate to Access Tokens
3. Verify token exists and is not expired
4. Check token has required scopes:
   - storage:buckets:read
   - storage:events:read
   - storage:metrics:read
   - storage:logs:read
   - storage:entities:read
5. Generate new token if needed
6. Update dashboard configuration

#### "400 Bad Request - Invalid tenant URL"

**Cause:** SSRF protection rejecting non-Dynatrace domain

**Solution:**
1. Verify tenant URL format: `https://xxx.apps.dynatrace.com`
2. For managed: `https://managed.company.com/e/environment-id`
3. Check domain is in whitelist (proxy_server.py:70)
4. Add custom domain if needed (requires code change)

**Valid Formats:**
- ✅ `https://abc123.apps.dynatrace.com`
- ✅ `https://abc123.live.dynatrace.com`
- ✅ `https://managed.company.com/e/12345678`
- ❌ `http://localhost:8080` (blocked by SSRF)
- ❌ `https://malicious.com` (not in whitelist)

#### CORS Errors

**Cause:** Browser blocking cross-origin request

**Solution:**
1. Verify proxy is running (check connection indicator)
2. Check proxy URL in configuration
3. Ensure proxy mode is selected (not direct connection)
4. Verify origin in ALLOWED_ORIGINS list

**Note:** Direct connection to Dynatrace API will NOT work due to CORS restrictions. Always use a proxy.

#### Tiles Show "No Data"

**Cause:** DQL query returns empty results or error

**Solution:**
1. Open browser DevTools console
2. Enable logging in dashboard Config
3. Check error messages
4. Copy DQL query
5. Test in Dynatrace Notebooks
6. Verify query returns expected fields:
   - Name field (entity name)
   - Status field (OK/WARN/ALERT)
   - Link field (optional URL)

**Debug Queries:**
```javascript
// In browser console with logging enabled
// Look for messages like:
Query results: [...]
Error executing query: ...
```

#### Encryption Not Working

**Cause:** Browser doesn't support Web Crypto API

**Solution:**
1. Check browser compatibility:
   - Chrome 37+
   - Firefox 34+
   - Safari 11+
   - Edge 79+
2. Ensure HTTPS or localhost (required for crypto API)
3. Check browser console for crypto errors

**Fallback:**
If Web Crypto API unavailable, dashboard will fall back to plaintext storage with warning message.

#### Lost API Key

**Cause:** API key only shown once at Python proxy startup

**Solution:**
1. Stop Python proxy (Ctrl+C)
2. Remove stored key file (if exists): `rm .proxy_api_key`
3. Restart: `python3 src/proxy_server.py`
4. Copy new key from console
5. Update dashboard configuration

**Persistent Key (Optional):**
```bash
export PROXY_API_KEY='your-secure-key-here'
python3 src/proxy_server.py
# Key will be reused on every startup
```

### Debug Mode

**Enable Logging:**
1. Open dashboard Config
2. Check "Enable Logging"
3. Save configuration
4. Reload page

**Console Output:**
```javascript
// Request logging
🔍 Executing DQL query: fetch events...
📤 Request: POST http://localhost:8081/api
📥 Response: 200 OK, 1234ms

// Error logging
❌ Error: Invalid query syntax
❌ Failed to load tile: tile1
```

**Python Proxy Logging:**
```bash
python3 src/proxy_server.py
# Console shows:
[2025-11-23 10:30:45] POST /api - 200 OK
[2025-11-23 10:30:46] Token hash: a1b2c3d4
[2025-11-23 10:30:47] Query executed in 234ms
```

### Performance Issues

**Slow Tile Loading:**
- Reduce auto-refresh interval
- Optimize DQL queries (add filters)
- Check Dynatrace API performance
- Reduce number of tiles

**Browser Freezing:**
- Check for infinite loops in custom code
- Verify no recursive function calls
- Test with logging disabled
- Clear browser cache

---

## Additional Resources

### Official Documentation
- **Dynatrace DQL:** https://docs.dynatrace.com/docs/platform/grail/dynatrace-query-language
- **Platform Tokens:** https://docs.dynatrace.com/docs/shortlink/platform-tokens
- **Web Crypto API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API

### Repository Documentation
- **README.md** - User setup guide
- **docs/SECURITY_REPORT.md** - Complete security audit
- **docs/SECURITY_FIXES_SUMMARY.md** - Implementation details
- **docs/ENCRYPTION_DETAILS.md** - Encryption specifications

### Useful Commands

**Start Development:**
```bash
python3 src/proxy_server.py
# Open http://localhost:8081
```

**Check Git Status:**
```bash
git status
git log --oneline -5
git branch -a
```

**Search Codebase:**
```bash
grep -n "function loadTileData" src/dashboard.html
grep -r "SSRF" docs/
```

**Validate HTML:**
```bash
# Open in browser and check DevTools console
# No red errors should appear
```

---

## Best Practices Summary

### Code Quality
✅ Read existing code before modifying
✅ Follow established patterns and conventions
✅ Add comments for complex logic
✅ Test changes thoroughly in browser
✅ Check DevTools console for errors

### Security
✅ Always sanitize user input
✅ Use safe DOM APIs
✅ Validate URLs and data
✅ Never log sensitive information
✅ Maintain encryption for credentials

### Git Workflow
✅ Work on Claude branches only
✅ Write descriptive commit messages
✅ Push to correct branch
✅ Test before committing

### Documentation
✅ Update relevant docs when making changes
✅ Add inline comments for complex code
✅ Note security implications
✅ Keep CLAUDE.md up to date

---

## Conclusion

This codebase is a **security-hardened, lightweight dashboard** with no external dependencies and a focus on simplicity. When making changes:

1. **Security First:** Never bypass security checks
2. **Simplicity:** No frameworks, no build step
3. **Browser Compatibility:** Test in modern browsers
4. **User Experience:** Fast, responsive, intuitive

For questions or clarifications, refer to the documentation in the `docs/` directory or examine the inline comments in the source code.

**Happy coding! 🚀**
