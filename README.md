# Simple External Dashboard

A lightweight, customizable dashboard for visualizing Dynatrace data through DQL queries. Features a fixed layout with 6 hexagonal tiles and 1 data table.

![](dashboard-sshot01.png)

The dashboard can run locally or on a public webserver using either a Python or PHP proxy. All settings are stored in the browser's localStorage and can be exported/imported.

## Files

| File | Description |
|------|-------------|
| `dashboard.html` | Main dashboard application |
| `proxy_server.py` | Python proxy for local use |
| `proxy.php` | PHP proxy for webserver deployment |

## Security Features

This dashboard includes comprehensive security enhancements:

- ✅ **Encrypted Storage:** API tokens and keys encrypted using AES-256-GCM with PBKDF2 (100k iterations)
- ✅ **Automatic Migration:** Legacy plaintext configs automatically upgraded with user notification
- ✅ **XSS Protection:** Multi-layered defense with DOMPurify sanitization, HTML encoding, and safe DOM APIs
- ✅ **API Key Authentication:** Proxy server requires X-API-Key header (constant-time verification)
- ✅ **SSRF Protection:** URL validation blocks private IPs, localhost, and non-Dynatrace domains
- ✅ **CORS Restrictions:** Whitelist-based origin validation (localhost only by default)
- ✅ **Secure Logging:** Tokens never exposed in logs (SHA256 hash for identification only)
- ✅ **Generic Error Messages:** No internal system details disclosed to clients
- ✅ **URL Validation:** Safe rendering with full URL validation and noopener/noreferrer
- ✅ **Safe Rendering:** Uses textContent and DOM APIs instead of innerHTML

**Security Status:** 8/9 vulnerabilities fixed (89% - only 2 low-priority issues remain)

For detailed security documentation, see:
- [SECURITY_REPORT.md](SECURITY_REPORT.md) - Complete audit findings and fixes
- [SECURITY_FIXES_SUMMARY.md](SECURITY_FIXES_SUMMARY.md) - Implementation details
- [ENCRYPTION_DETAILS.md](ENCRYPTION_DETAILS.md) - Encryption technical specs

## Quick Start

### Option A: Local Setup (Python Proxy)

**Requirements:** Python 3

1. Place `dashboard.html` and `proxy_server.py` in the same folder

2. Start the proxy server:
   ```bash
   python3 proxy_server.py
   ```

3. **IMPORTANT:** The server will display a generated **API Key** in the console - **COPY IT NOW!**
   ```
   🔑 Generated new API key - COPY THIS NOW:

      [YOUR-API-KEY-HERE]

   📋 Configure this key in the dashboard 'Python Proxy API Key' field
   ```
   The API key is shown **only once** for security reasons.

4. Open `http://localhost:8081` in your browser

5. Click **⚙️ Config** and enter:
   - **Proxy Mode:** Python Proxy
   - **Python Proxy URL:** `http://localhost:8081`
   - **Python Proxy API Key:** Paste the API key from step 3
   - **Tenant URL:** `https://xxx.apps.dynatrace.com` (or your managed URL)
   - **API Token:** Your Dynatrace API token

6. Click **Save**

**Using a Persistent API Key (Optional):**

To avoid generating a new key each time, set an environment variable:
```bash
export PROXY_API_KEY='your-secure-key-here'
python3 proxy_server.py
```

The proxy will use this key instead of generating a new one.

### Option B: Webserver Setup (PHP Proxy)

**Requirements:** PHP-enabled webserver

1. Configure `proxy.php` by editing the API key:
   ```php
   define('PROXY_API_KEY', 'YOUR_SECRET_KEY');
   ```

2. Upload files to your webserver:
   ```
   /public_html/
     ├── dashboard.html
     └── proxy.php
   ```

3. Open `https://your-domain.com/dashboard.html` in your browser

4. Click **Config** and enter:
   - **Proxy Mode:** PHP Proxy
   - **PHP Proxy URL:** `https://your-domain.com/proxy.php`
   - **Proxy API Key:** Same key configured in proxy.php
   - **Tenant URL:** `https://xxx.apps.dynatrace.com`
   - **API Token:** Your Dynatrace token

5. Click **Save**

## Dashboard Configuration

### Hexagonal Tiles

Click the settings icon on any tile to configure its query and field mappings. Queries must return: name, status (OK/WARN/ALERT), and optionally a link.

### Events Table

Click the settings icon on the table to customize its DQL query.

### Global Variables

Define reusable variables via the **Variables** button. Reference them in queries using the `${{VARIABLE_NAME}}` syntax.

### Export/Import

Use **Config > Export** to save all settings as JSON, and **Config > Import** to restore them.

## Dynatrace Token

This dashboard requires a Platform Token. See the [Dynatrace documentation](https://docs.dynatrace.com/docs/shortlink/platform-tokens) for details.

Assign scopes based on your query requirements:

- `storage:buckets:read`
- `storage:events:read`
- `storage:metrics:read`
- `storage:logs:read`
- `storage:entities:read`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Red status indicator | Verify the proxy is running on the correct port |
| 401 Unauthorized (Proxy) | **Check Python Proxy API Key** - Restart proxy to see key in console, then copy to dashboard config |
| 401 Unauthorized (Dynatrace) | Check Dynatrace API Token is valid and not expired |
| 403 Forbidden | Verify Dynatrace token permissions include required scopes (storage:*:read) |
| 400 Bad Request - "Invalid tenant URL" | **SSRF Protection:** Only Dynatrace domains allowed (*.dynatrace.com, *.dynatracelabs.com). Check Tenant URL format |
| CORS Error | Ensure you're using a proxy, not direct connection to Dynatrace |
| Empty data | Validate your DQL query in the Dynatrace console first |
| "API key is required" | Configure the Python Proxy API Key in dashboard settings (⚙️ Config) |
| Lost API Key | Restart the proxy server - it will generate and display a new key |
| 502 Service Error | Check proxy logs for details (enable logging in dashboard settings) |
| Security upgrade notification | Normal - your old plaintext credentials were automatically encrypted |

## Notes

- Auto-refresh interval is configurable from 30 seconds to 60 minutes
- PHP proxy includes rate limiting (30 requests/minute per IP)
- All settings persist in browser localStorage (encrypted with AES-256-GCM)
- Python proxy requires API key authentication for security
- Legacy configs are automatically migrated to encrypted format
- Tokens are never exposed in logs (SHA256 hash shown for identification)

## Security Considerations

⚠️ **Important Security Notes:**

### ✅ Implemented Protections

1. **Encrypted Storage (AES-256-GCM):**
   - All API tokens and proxy keys encrypted using AES-256-GCM with PBKDF2 (100,000 iterations)
   - Random salt per browser instance, random IV per encryption operation
   - Automatic migration of legacy plaintext configurations
   - Note: Determined attackers with browser access could potentially decrypt data

2. **XSS Protection (Multi-Layered):**
   - DOMPurify sanitization for all user inputs
   - HTML encoding before markdown processing
   - Safe DOM APIs (createElement, textContent) instead of innerHTML
   - URL validation with full scheme checking
   - Links opened with noopener/noreferrer flags

3. **SSRF Protection:**
   - URL validation blocks private IPs (10.x, 192.168.x, 172.16-31.x)
   - Localhost and loopback addresses blocked (127.0.0.1, ::1)
   - Cloud metadata service blocked (169.254.169.254)
   - Whitelist approach: Only Dynatrace domains allowed (*.dynatrace.com, etc.)

4. **Secure Logging:**
   - API tokens never exposed in logs (SHA256 hash for identification only)
   - Proxy API key shown only once during generation
   - Detailed errors logged server-side only (generic messages to clients)

5. **API Authentication:**
   - Python proxy requires X-API-Key header for all requests
   - Constant-time comparison prevents timing attacks
   - 401 Unauthorized returned for missing/invalid keys

6. **CORS Restrictions:**
   - Whitelist-based origin validation (localhost only by default)
   - No wildcard origins allowed
   - Modify `ALLOWED_ORIGINS` in `proxy_server.py` if needed

### ⚠️ Deployment Considerations

1. **Python Proxy:** Generates a random API key on startup. For persistent keys, set `PROXY_API_KEY` environment variable.

2. **Network Exposure:** Do NOT expose the Python proxy to the public internet without:
   - Reverse proxy with HTTPS (nginx, Apache)
   - Firewall rules
   - Additional authentication layer
   - Rate limiting

3. **Production Use:** For production environments, implement:
   - Proper backend service with OAuth/JWT
   - Server-side session management
   - Database-backed credential storage
   - Comprehensive audit logging
   - Rate limiting and DDoS protection

4. **Token Permissions:** Follow principle of least privilege - grant only required Dynatrace scopes.

### 📊 Security Status

- **8/9 vulnerabilities fixed** (89% complete)
- All critical (P0) issues resolved
- Only 2 low-priority issues remain (Path Traversal with hardcoded paths, Rate Limiting)

For comprehensive security documentation:
- [SECURITY_REPORT.md](SECURITY_REPORT.md) - Complete audit report with fix status
- [SECURITY_FIXES_SUMMARY.md](SECURITY_FIXES_SUMMARY.md) - Detailed implementation guide
- [ENCRYPTION_DETAILS.md](ENCRYPTION_DETAILS.md) - Technical encryption specifications

## Requirements

- Python 3.6+ (for local proxy)
- PHP 7.0+ with cURL extension (for PHP proxy)


## License

MIT License - See [LICENSE](LICENSE) for details.
