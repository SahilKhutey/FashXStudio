# Image Fetch Security

## 1. Network Hardening Standards

The `SafeImageFetcher` enforces defense-in-depth against Server-Side Request Forgery (SSRF), DNS rebinding, resource exhaustion, and credential leakage:

1. **Protocol Strictness**: Only `https://` is permitted. Plaintext `http://`, `ftp://`, or `file://` URLs are rejected immediately.
2. **Approved Host Allowlist**: If configured on the catalog source, outbound downloads are restricted strictly to permitted hostnames.
3. **SSRF Filtering**: Outbound target hosts are pre-resolved and checked against prohibited IP subnets:
   - Loopback: `127.0.0.0/8`, `::1`
   - Private networks: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
   - Link-local: `169.254.0.0/16`, `fe80::/10`
   - Cloud metadata: `169.254.169.254`
   - Multicast: `224.0.0.0/4`
4. **DNS Rebinding Protection**: Re-verifies IP addresses at connection time to defeat dynamic DNS rebinding exploits.
5. **Redirect Policy**: Redirects are disabled by default. If enabled for partner feeds, each redirect target is independently validated against SSRF rules and allowlists.
6. **Streaming Size Bounds**: Streams chunked responses and aborts immediately if payload exceeds 10 MB.
7. **Timeout Safeguards**: Connect timeout (5s), read timeout (15s), total timeout (30s).
8. **Credential & Secret Redaction**: Error logs, traces, and metrics strip query parameters and authentication headers.
