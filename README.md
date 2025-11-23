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

This dashboard includes multiple security enhancements:

- ✅ **XSS Protection:** DOMPurify sanitization for all user inputs
- ✅ **API Key Authentication:** Proxy server requires authentication
- ✅ **CORS Restrictions:** Limited to localhost origins
- ✅ **URL Validation:** Only HTTPS links are allowed
- ✅ **Secure Rendering:** Uses textContent instead of innerHTML for user data

## Quick Start

### Option A: Local Setup (Python Proxy)

**Requirements:** Python 3

1. Place `dashboard.html` and `proxy_server.py` in the same folder
2. Start the proxy server:
   ```bash
   python3 proxy_server.py
   ```
   The server will display an **API Key** - copy this key!

3. Open `http://localhost:8081` in your browser
4. Click **Config** and enter:
   - **Proxy Mode:** Python Proxy
   - **Python Proxy URL:** `http://localhost:8081`
   - **Python Proxy API Key:** Paste the API key from step 2
   - **Tenant URL:** `https://xxx.apps.dynatrace.com`
   - **API Token:** Your Dynatrace token
5. Click **Save**

**Note:** To use a persistent API key across restarts:
```bash
export PROXY_API_KEY='your-secure-key-here'
python3 proxy_server.py
```

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
| Red status indicator | Verify the proxy is running |
| 401 Unauthorized | **Check Python Proxy API Key** - Copy from proxy console and paste in dashboard config |
| 401 Error (Dynatrace) | Check Dynatrace API Token is valid |
| 403 Error | Verify Dynatrace token permissions include required scopes |
| CORS Error | Ensure you're using a proxy, not direct connection |
| Empty data | Validate your DQL query in the Dynatrace console |
| "API key is required" | Configure the Python Proxy API Key in dashboard settings |

## Notes

- Auto-refresh interval is configurable from 30 seconds to 60 minutes
- PHP proxy includes rate limiting (30 requests/minute per IP)
- All settings persist in browser localStorage
- Python proxy now requires API key authentication for security

## Security Considerations

⚠️ **Important Security Notes:**

1. **API Keys Storage:** Dynatrace API tokens are stored in browser localStorage. For production use, consider implementing a backend service.

2. **Python Proxy:** The proxy generates a random API key on startup. Set `PROXY_API_KEY` environment variable for persistent keys.

3. **Network Exposure:** Do not expose the Python proxy to the public internet without additional security measures (HTTPS, firewall rules, etc.).

4. **XSS Protection:** The dashboard uses DOMPurify to sanitize all user inputs, but avoid pasting untrusted DQL queries.

5. **CORS:** The Python proxy restricts CORS to localhost by default. Modify `ALLOWED_ORIGINS` in `proxy_server.py` if needed.

For a detailed security analysis, see [SECURITY_REPORT.md](SECURITY_REPORT.md).

## Requirements

- Python 3.6+ (for local proxy)
- PHP 7.0+ with cURL extension (for PHP proxy)


## License

MIT License - See [LICENSE](LICENSE) for details.
