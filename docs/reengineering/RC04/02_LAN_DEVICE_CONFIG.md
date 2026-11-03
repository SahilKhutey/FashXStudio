# RC-04 — LAN Configuration & Physical Device Setup

## Context (FX-005)
Physical mobile testing requires the smartphone running Expo Go to reach the development machine's FastAPI server over Wi-Fi. If the development machine IP changes (e.g. moving between networks), `mobile/.env` becomes stale and network requests fail silently.

## Automated Utility: `configure_lan_api.py`

### Usage
```bash
# Check connectivity and view current IP (Dry run)
python scripts/mobile/configure_lan_api.py

# Apply detected IP to mobile/.env
python scripts/mobile/configure_lan_api.py --apply
```

### Execution Output
```
=== FashXStudio Mobile LAN Configuration Utility ===
Detected LAN IPv4: 10.178.234.242
Target Mobile API: http://10.178.234.242:8000
Backend Status:   ONLINE & REACHABLE at http://10.178.234.242:8000/healthz/live

[APPLIED] Successfully updated 'mobile\.env' -> EXPO_PUBLIC_API_URL=http://10.178.234.242:8000
```

### Evaluator Walkthrough on Physical Smartphone
1. Connect mobile phone to the same Wi-Fi network as development workstation.
2. Run `python scripts/mobile/configure_lan_api.py --apply`.
3. In a separate shell: `cd mobile && npx expo start --lan`.
4. Scan the rendered QR code with the Expo Go app (Android) or iOS Camera app.
5. The mobile client will connect directly to the running backend service.
