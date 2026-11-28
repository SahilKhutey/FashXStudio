# 17 — Device Verification Checklist

All physical-device checks are `PENDING` (no physical Android/iOS device or EAS cloud build session in this environment):
- [ ] Android EAS development/staging APK installs and launches with `com.fashxstudio.app.dev` / `.staging`
- [ ] iOS EAS development/staging IPA installs and launches with `com.fashxstudio.app.dev` / `.staging`
- [ ] Environment indicator displays `DEVELOPMENT` / `STAGING` and is hidden in `PRODUCTION`
- [ ] Camera permission prompt appears only upon entering capture flow; denial & blocked states recover cleanly
- [ ] Captured photo previews locally without auto-upload
- [ ] SecureStore session survives app restart and clears completely on logout
- [ ] Staging API smoke test passes for login, catalog, search, fit, and VTO
