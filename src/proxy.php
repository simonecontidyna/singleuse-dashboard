<?php
/**
 * Proxy PHP Sicuro per Dynatrace API - Bypass CORS
 * File: proxy.php
 * 
 * IMPORTANTE: Genera una chiave segreta e configurala qui sotto
 */

// Imposta header CORS immediatamente, prima di qualsiasi altra cosa
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Proxy-API-Key');
header('Content-Type: application/json');

// ========== CONFIGURAZIONE SICUREZZA ==========
// Genera una chiave lunga e casuale, esempio: openssl rand -hex 32
define('PROXY_API_KEY', 'CAMBIA_QUESTA_CHIAVE_CON_UNA_SICURA');

// Lista domini autorizzati (opzionale, lascia vuoto per accettare tutti)
$ALLOWED_ORIGINS = [
    // 'https://tuo-dominio-aruba.it',
    // 'https://www.tuo-dominio-aruba.it'
];
// ==============================================

// Verifica API Key
function verifyApiKey() {
    global $PROXY_API_KEY;
    
    if (PROXY_API_KEY === 'CAMBIA_QUESTA_CHIAVE_CON_UNA_SICURA') {
        http_response_code(500);
        echo json_encode([
            'error' => 'Configuration error',
            'message' => 'Proxy API key not configured'
        ]);
        exit();
    }
    
    // Cerca l'API key negli header
    $providedKey = null;
    if (isset($_SERVER['HTTP_X_PROXY_API_KEY'])) {
        $providedKey = $_SERVER['HTTP_X_PROXY_API_KEY'];
    } elseif (isset($_GET['api_key'])) {
        // Fallback per test (non consigliato in produzione)
        $providedKey = $_GET['api_key'];
    }
    
    if (!$providedKey || !hash_equals(PROXY_API_KEY, $providedKey)) {
        http_response_code(401);
        echo json_encode([
            'error' => 'Unauthorized',
            'message' => 'Invalid or missing API key'
        ]);
        
        // Log tentativo non autorizzato
        error_log('Unauthorized proxy access attempt from ' . $_SERVER['REMOTE_ADDR']);
        exit();
    }
}

// Verifica origine (se configurato)
function checkOrigin() {
    global $ALLOWED_ORIGINS;
    
    if (empty($ALLOWED_ORIGINS)) {
        // Nessun filtro origine configurato
        header('Access-Control-Allow-Origin: *');
        return;
    }
    
    $origin = isset($_SERVER['HTTP_ORIGIN']) ? $_SERVER['HTTP_ORIGIN'] : '';
    
    if (in_array($origin, $ALLOWED_ORIGINS)) {
        header('Access-Control-Allow-Origin: ' . $origin);
    } else {
        http_response_code(403);
        echo json_encode([
            'error' => 'Forbidden',
            'message' => 'Origin not allowed'
        ]);
        exit();
    }
}

// Gestisci richieste OPTIONS (preflight) - deve essere prima di tutto
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Health check endpoint (pubblico, senza autenticazione)
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (strpos($_SERVER['REQUEST_URI'], '/health') !== false) {
        echo json_encode([
            'status' => 'healthy',
            'message' => 'Secure PHP Proxy is running',
            'auth_required' => true
        ]);
        exit();
    }
}

// Verifica autenticazione per tutte le altre richieste
verifyApiKey();

// Gestisci solo richieste POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit();
}

// Rate limiting: 30 richieste al minuto per IP
$rate_limit_file = sys_get_temp_dir() . '/proxy_rate_limit_' . md5($_SERVER['REMOTE_ADDR']);
$rate_limit_max = 30; // Richieste
$rate_limit_window = 60; // Secondi (1 minuto)

if (file_exists($rate_limit_file)) {
    $rate_data = json_decode(file_get_contents($rate_limit_file), true);
    $current_time = time();
    
    // Pulisci richieste vecchie (fuori dalla finestra temporale)
    $rate_data['requests'] = array_filter($rate_data['requests'], function($timestamp) use ($current_time, $rate_limit_window) {
        return ($current_time - $timestamp) < $rate_limit_window;
    });
    
    // Controlla se ha superato il limite
    if (count($rate_data['requests']) >= $rate_limit_max) {
        http_response_code(429);
        echo json_encode([
            'error' => 'Rate limit exceeded',
            'message' => "Maximum $rate_limit_max requests per minute"
        ]);
        exit();
    }
    
    // Aggiungi questa richiesta
    $rate_data['requests'][] = $current_time;
} else {
    $rate_data = ['requests' => [time()]];
}

file_put_contents($rate_limit_file, json_encode($rate_data));

// Leggi il body della richiesta
$input = file_get_contents('php://input');
$requestData = json_decode($input, true);

if (!$requestData) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit();
}

// Estrai parametri
$dynatraceUrl = isset($requestData['url']) ? rtrim($requestData['url'], '/') : null;
$apiToken = isset($requestData['token']) ? $requestData['token'] : null;
$query = isset($requestData['query']) ? $requestData['query'] : null;
$timeframe = isset($requestData['timeframe']) ? $requestData['timeframe'] : null;

if (!$dynatraceUrl || !$apiToken || !$query) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required parameters']);
    exit();
}

// Valida che l'URL sia un dominio Dynatrace valido
if (!preg_match('/^https:\/\/[a-zA-Z0-9\-]+\.(live\.dynatrace\.com|apps\.dynatrace\.com)/', $dynatraceUrl)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid Dynatrace URL']);
    exit();
}

// Prepara la richiesta a Dynatrace
$apiUrl = $dynatraceUrl . '/platform/storage/query/v1/query:execute';

$requestBody = [
    'query' => $query,
    'requestTimeoutMilliseconds' => 30000,
    'enablePreview' => false,
    'fetchTimeoutSeconds' => 60
];

// Aggiungi timeframe se presente
if ($timeframe) {
    $requestBody['defaultTimeframeStart'] = $timeframe['start'];
    $requestBody['defaultTimeframeEnd'] = $timeframe['end'];
}

// Configura cURL
$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($requestBody));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Authorization: Bearer ' . $apiToken,
    'Content-Type: application/json'
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 60);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);

// Esegui la richiesta
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError = curl_error($ch);
curl_close($ch);

// Gestisci errori cURL
if ($curlError) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Proxy error',
        'message' => 'Failed to connect to Dynatrace'
    ]);
    exit();
}

// Gestisci risposta Dynatrace
if ($httpCode >= 400) {
    http_response_code($httpCode);
    echo $response;
    exit();
}

// Ritorna la risposta
http_response_code(200);
echo $response;
?>
