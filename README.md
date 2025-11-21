# 📊 Dynatrace Dashboard

Dashboard con layout rigido (6 tiles a esagoni + 1 tabella) per visualizzare dati Dynatrace da query DQL personalizzabili.
Può essere eseguita localmente o su webserver pubblico usando un proxy python o php, le impostazioni vengono salvate nel localstorage del browser
e sono esportabili e reimportabili.
---

## 📦 File Inclusi

| File | Descrizione |
|------|-------------|
| `dashboard.html` | Dashboard principale |
| `proxy_server.py` | Proxy Python per uso locale |
| `proxy.php` | Proxy PHP per webserver |

---

##  Guida Rapida

### Opzione A: Uso Locale (Python Proxy)

**Requisiti:** Python 3 installato

1. Metti `dashboard.html` e `proxy_server.py` nella stessa cartella
2. Apri terminale e avvia il proxy:
   ```bash
   python3 proxy_server.py
   ```
3. Apri nel browser: `http://localhost:8081`
4. Clicca ⚙️ **Config** e compila:
   - **Modalità Proxy:** Python Proxy
   - **URL Tenant:** `https://xxx.apps.dynatrace.com`
   - **API Token:** Il tuo token Dynatrace
5. Clicca **Salva**

---

### Opzione B: Webserver (PHP Proxy)

**Requisiti:** Webserver in hosting che supporti PHP

1. **Configura proxy.php:**
   - Apri `proxy.php` e modifica la riga:
     ```php
     define('PROXY_API_KEY', 'LA_TUA_CHIAVE_SEGRETA');
     ```

2. **Carica i file** sul webserver:
   ```
   /public_html/
     ├── dashboard.html
     └── proxy.php
   ```

3. **Apri la dashboard** nel browser: `https://tuo-dominio.com/dashboard.html`

4. Clicca ⚙️ **Config** e compila:
   - **Modalità Proxy:** PHP Proxy
   - **URL Proxy PHP:** `https://tuo-dominio.com/proxy.php`
   - **Proxy API Key:** La stessa chiave configurata in proxy.php
   - **URL Tenant:** `https://xxx.live.dynatrace.com`
   - **API Token:** Il tuo token Dynatrace

5. Clicca **Salva**

---

## ⚙️ Configurazione Dashboard

### Tile Esagonali
- Clicca ⚙️ su un tile per configurare query e campi
- La query deve restituire: nome, stato (OK/WARN/ALERT), link (opzionale)

### Tabella Eventi
- Clicca ⚙️ sulla tabella per personalizzare la query

### Variabili Globali
- Clicca 🔧 **Variabili** per definire variabili riutilizzabili
- Usa `${{NOME_VARIABILE}}` nelle query

### Esporta/Importa
- ⚙️ Config → **Esporta** per salvare tutte le impostazioni
- ⚙️ Config → **Importa** per ripristinarle

---

## 🔑 Token Dynatrace

Necessita di un Platform Token token: https://docs.dynatrace.com/docs/shortlink/platform-tokens
Assegnare gli Scope necessari in base alle query che verranno usate nella dashboard, ad esempio:
storage:buckets:read, storage:events:read, storage:metrics:read, storage:logs:read, storage:entities:read
---

## ❓ Risoluzione Problemi

| Problema | Soluzione |
|----------|-----------|
| Indicatore rosso | Verifica che il proxy sia avviato |
| Errore 401 | Controlla API Token o Proxy API Key |
| Errore 403 | Verifica permessi token Dynatrace |
| Errore CORS | Usa il proxy, non la connessione diretta |
| Dati vuoti | Controlla la query DQL nella console Dynatrace |

---

## 📝 Note

- Il **refresh automatico** è configurabile da 30 secondi a 60 minuti
- Il **PHP Proxy** ha rate limiting di 30 richieste/minuto per IP
- Le impostazioni sono salvate nel browser (localStorage)
