# Configuration Conflict Handling
Concurrency conflict resolution:
- The server checks `If-Match: "revision-N"`.
- If another user saved revision N+1, the server returns 409 Conflict.
- The editor alerts the user to reload the latest server draft before overwriting.
