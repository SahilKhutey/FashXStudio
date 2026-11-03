# RC-01 — Mobile Client Connectivity Guide

## Network Topology & Address Resolution

Mobile applications running on physical devices or emulators cannot reach `127.0.0.1` on the development host:
- **Android Emulator**: `10.0.2.2:8000` routes to host loopback `127.0.0.1:8000`.
- **iOS Simulator**: `127.0.0.1:8000` routes to host loopback.
- **Physical Device (Expo Go / Development Build)**: Requires host LAN IP (e.g. `192.168.1.X:8000`).

## Host Server Binding
The FastAPI development server must bind to all network interfaces (`0.0.0.0`):
```powershell
.venv\Scripts\uvicorn fashx.main:app --host 0.0.0.0 --port 8000 --reload
```
Verification confirmed active listening on `0.0.0.0:8000` via Windows netstat.

## Cross-Origin Resource Sharing (CORS)
Configured in `backend/fashx/main.py`:
- Allowed Origins: `*` (or local Expo origins `http://localhost:8081`, `http://192.168.*:*`).
- Allowed Methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`.
- Allowed Headers: `Authorization`, `Content-Type`, `X-Requested-With`, `Accept`.

## Mobile Environment Variable (`EXPO_PUBLIC_API_URL`)
To configure the Expo application to target the backend:
1. Create or update `mobile/.env`:
   ```bash
   EXPO_PUBLIC_API_URL=http://<YOUR_HOST_LAN_IP>:8000
   ```
2. For Android emulator testing:
   ```bash
   EXPO_PUBLIC_API_URL=http://10.0.2.2:8000
   ```

## Connectivity Diagnostic Checklist
```bash
# Test connectivity from host terminal
curl http://127.0.0.1:8000/api/v1/health

# Test connectivity from LAN
curl http://<YOUR_HOST_LAN_IP>:8000/api/v1/health
```
Expected response:
```json
{"status": "ok"}
```
