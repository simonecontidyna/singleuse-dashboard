#!/usr/bin/env python3
"""
Proxy server per bypassare CORS con Dynatrace API
Avvia con: python3 proxy_server.py

Security features:
- API key authentication (set via PROXY_API_KEY env variable)
- CORS restrictions
- URL validation
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse
import os
import secrets
import hashlib

# Generate or load API key
# Priority: Environment variable > Generated key
API_KEY = os.environ.get('PROXY_API_KEY')
if not API_KEY:
    # Generate a secure random API key
    API_KEY = secrets.token_urlsafe(32)
    print(f"\n⚠️  No PROXY_API_KEY environment variable found.")
    print(f"🔑 Generated new API key - COPY THIS NOW:")
    print(f"\n   {API_KEY}\n")
    print(f"📋 Configure this key in the dashboard 'Python Proxy API Key' field")
    print(f"💾 To make it persistent, set environment variable:")
    print(f"   export PROXY_API_KEY='{API_KEY}'")
    print()

# Allowed origins for CORS (more restrictive than *)
ALLOWED_ORIGINS = [
    'http://localhost:8081',
    'http://127.0.0.1:8081',
    'http://localhost:3000',  # For development
    'http://127.0.0.1:3000',
]

def is_valid_dynatrace_url(url):
    """
    Validate that the URL is a legitimate Dynatrace tenant URL.
    Prevents SSRF attacks by blocking private IPs and non-Dynatrace domains.
    """
    try:
        parsed = urlparse(url)

        # Must be HTTP or HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False

        # Extract hostname
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block localhost and loopback
        if hostname in ['localhost', '127.0.0.1', '::1', '0.0.0.0']:
            return False

        # Block private IP ranges
        import ipaddress
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
            # Block cloud metadata services
            if hostname == '169.254.169.254':
                return False
        except ValueError:
            # Not an IP address, check domain
            pass

        # Validate Dynatrace domains
        valid_domains = [
            '.dynatrace.com',
            '.dynatracelabs.com',
            '.sprint.dynatracelabs.com',
            '.dynatrace.managed',
            '.dynatrace-managed.com',
        ]

        # Check if hostname ends with valid Dynatrace domain
        is_dynatrace_domain = any(hostname.endswith(domain) for domain in valid_domains)

        # Also allow exact match for managed instances (e.g., "abc123.managed-xxx.dynalabs.io")
        is_managed_instance = '.managed' in hostname and any(
            tld in hostname for tld in ['.dynatrace.com', '.dynalabs.io', '.dynatracelabs.com']
        )

        return is_dynatrace_domain or is_managed_instance

    except Exception:
        return False

class CORSProxyHandler(BaseHTTPRequestHandler):
    def verify_api_key(self):
        """Verify X-API-Key header using constant-time comparison"""
        provided_key = self.headers.get('X-API-Key', '')

        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(provided_key, API_KEY)

    def get_allowed_origin(self):
        """Get the origin if it's in the allowed list"""
        origin = self.headers.get('Origin', '')
        if origin in ALLOWED_ORIGINS:
            return origin
        # Default to first allowed origin if not found
        return ALLOWED_ORIGINS[0]

    def do_GET(self):
        """Gestisce richieste GET per health check e dashboard"""
        if self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'healthy',
                'message': 'Python Proxy is running'
            }).encode('utf-8'))
            return
            
        if self.path == '/' or self.path == '/dashboard.html':
            try:
                # Cerca il file dashboard.html nella stessa directory dello script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                html_path = os.path.join(script_dir, 'dashboard.html')
                
                if not os.path.exists(html_path):
                    # Prova nella directory corrente
                    html_path = 'dashboard.html'
                
                with open(html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', len(content.encode('utf-8')))
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, "Resource not found")
        else:
            self.send_error(404, "Resource not found")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        # Solo /api gestisce le richieste proxy
        if self.path != '/api':
            self.send_error(404, "Resource not found")
            return

        # Verify API key authentication
        if not self.verify_api_key():
            self.send_response(401)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Unauthorized',
                'message': 'Valid X-API-Key header required'
            }).encode('utf-8'))
            return

        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Estrai i parametri dalla richiesta
            dynatrace_url = request_data.get('url')
            api_token = request_data.get('token')
            query = request_data.get('query')
            enable_logging = request_data.get('enableLogging', False)
            tile_title = request_data.get('tileTitle', 'Unknown')
            
            if not all([dynatrace_url, api_token, query]):
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Bad Request',
                    'message': 'Invalid request format'
                }).encode('utf-8'))
                return

            # Validate Dynatrace URL to prevent SSRF attacks
            if not is_valid_dynatrace_url(dynatrace_url):
                self.send_response(400)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Bad Request',
                    'message': 'Invalid tenant URL'
                }).encode('utf-8'))
                return

            # Pulisci l'URL rimuovendo trailing slashes e doppi slash
            dynatrace_url = dynatrace_url.rstrip('/')
            
            # Prepara la richiesta a Dynatrace usando l'endpoint Grail corretto
            api_url = f"{dynatrace_url}/platform/storage/query/v1/query:execute"
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            # Formato richiesta per Grail Query API
            request_body = {
                'query': query,
                'requestTimeoutMilliseconds': 30000,
                'enablePreview': False,
                'fetchTimeoutSeconds': 60
            }
            
            # Aggiungi timeframe se presente nella richiesta
            if 'timeframe' in request_data:
                timeframe = request_data['timeframe']
                if timeframe:
                    request_body['defaultTimeframeStart'] = timeframe.get('start')
                    request_body['defaultTimeframeEnd'] = timeframe.get('end')
            
            data = json.dumps(request_body).encode('utf-8')
            req = urllib.request.Request(api_url, data=data, headers=headers, method='POST')
            
            # 🔍 LOG REQUEST (solo se abilitato)
            if enable_logging:
                # Hash token for security
                token_hash = hashlib.sha256(api_token.encode()).hexdigest()[:8]
                print("\n" + "="*80)
                print("📤 REQUEST to Dynatrace:")
                print("="*80)
                print(f"URL: {api_url}")
                print(f"Method: POST")
                print(f"Headers:")
                print(f"  Authorization: Bearer [REDACTED-{token_hash}]")
                print(f"  Content-Type: application/json")
                print(f"\nRequest Body:")
                print(json.dumps(request_body, indent=2))
                print("="*80)
            
            # Esegui la richiesta
            with urllib.request.urlopen(req, timeout=60) as response:
                response_data = response.read()
                result = json.loads(response_data.decode('utf-8'))
                
                # 🔍 LOG RESPONSE (solo se abilitato)
                if enable_logging:
                    print("\n" + "="*80)
                    print("📥 RESPONSE from Dynatrace:")
                    print("="*80)
                    print(f"Status: {response.status}")
                    print(f"Response Body:")
                    print(json.dumps(result, indent=2))
                    print("="*80 + "\n")
                
                # La Grail API può restituire uno stato "RUNNING" se la query non è ancora completa
                # In questo caso dovremmo fare polling, ma per semplicità aspettiamo il timeout
                if result.get('state') == 'RUNNING':
                    # Se la query è ancora in esecuzione, restituisci un risultato vuoto
                    result = {'state': 'RUNNING', 'records': [], 'result': {'records': []}}
                
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
                # Log conciso inline (sempre attivo se logging non è abilitato)
                if not enable_logging:
                    grail = result.get('result', {}).get('metadata', {}).get('grail', {})
                    if grail:
                        def format_bytes(bytes_val):
                            if not bytes_val: return "0B"
                            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                                if bytes_val < 1024: return f"{bytes_val:.1f}{unit}"
                                bytes_val /= 1024.0
                            return f"{bytes_val:.1f}PB"
                        
                        exec_time = grail.get('executionTimeMilliseconds', 0)
                        scanned_bytes = format_bytes(grail.get('scannedBytes', 0))
                        scanned_records = grail.get('scannedRecords', 0)
                        query_id = grail.get('queryId', 'N/A')[:8]  # Solo primi 8 caratteri
                        
                        # Log inline conciso
                        print(f'[PROXY] {self.address_string()} - "POST /api HTTP/1.1" 200 - [{tile_title}] {exec_time}ms | {scanned_bytes} | {scanned_records} rec | ID:{query_id}')
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)

            # 🔍 LOG ERROR (solo se abilitato)
            if enable_logging:
                print("\n" + "="*80)
                print("❌ HTTP ERROR from Dynatrace:")
                print("="*80)
                print(f"Status Code: {e.code}")
                print(f"Reason: {e.reason}")
                print(f"Error Body:")
                print(error_body)
                print("="*80 + "\n")

            # Return generic error to client (don't expose backend details)
            self.send_response(502)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Service Error',
                'message': 'Unable to process request'
            }).encode('utf-8'))
            
        except Exception as e:
            # 🔍 LOG EXCEPTION (solo se abilitato - usa la variabile dalla request se disponibile)
            try:
                if enable_logging:
                    print("\n" + "="*80)
                    print("❌ PROXY EXCEPTION:")
                    print("="*80)
                    print(f"Exception Type: {type(e).__name__}")
                    print(f"Exception Message: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    print("="*80 + "\n")
            except:
                pass  # enable_logging potrebbe non essere definita in caso di errore early

            # Return generic error to client (don't expose internal details)
            self.send_response(500)
            self.send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }).encode('utf-8'))

    def send_cors_headers(self):
        # Use allowed origin instead of wildcard
        allowed_origin = self.get_allowed_origin()
        self.send_header('Access-Control-Allow-Origin', allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        self.send_header('Access-Control-Allow-Credentials', 'true')

    def log_message(self, format, *args):
        # Log personalizzato - viene chiamato automaticamente dopo ogni risposta
        # Estrarre info aggiuntive se disponibili
        pass  # Non facciamo nulla qui, gestiamo i log manualmente nel do_POST

def run_proxy(port=8081):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSProxyHandler)
    # Display only hash for security (as identifier, not for authentication)
    key_hash = hashlib.sha256(API_KEY.encode()).hexdigest()[:8]
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           Dynatrace CORS Proxy Server Avviato                ║
╚══════════════════════════════════════════════════════════════╝

🚀 Server in ascolto su: http://localhost:{port}
📊 Apri il browser su: http://localhost:{port}/
🔌 API Proxy endpoint: http://localhost:{port}/api

🔐 SECURITY ENABLED:
   API Key (hash): {key_hash}...

   ℹ️  Configure the full API key in dashboard settings
   💾 For persistent key: set PROXY_API_KEY environment variable

⏹️  Premi Ctrl+C per fermare il server

""")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✋ Server arrestato dall'utente")
        httpd.shutdown()

if __name__ == '__main__':
    run_proxy(8081)
