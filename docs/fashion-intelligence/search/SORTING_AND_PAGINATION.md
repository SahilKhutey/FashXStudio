# Sorting and Cursor-Based Pagination Specification

## 1. Supported Sorting Modes
Clients can only sort using explicit allowed values:
- `relevance`: Final hybrid score (RRF + business boosts).
- `price_low`: Lowest active offer price first.
- `price_high`: Highest active offer price first.
- `newest`: Most recently ingested products first.
- `recently_updated`: Most recently verified active offers first.
- `popularity`: Interaction click/save engagement rank (when reliable data exists).
- `similarity`: Raw vector cosine similarity (for pure semantic/visual queries).

Arbitrary user-provided SQL column sorting is strictly rejected to prevent SQL injection.

---

## 2. Cursor-Based Pagination Architecture
Offset-based pagination (`OFFSET N`) suffers from:
- Deep page scan performance degradation ($O(N)$ execution cost).
- "Result shift" and duplicates if the catalog changes between page requests.

FashXStudio implements **opaque cursor tokens**:
1. When a query is executed, the ordered candidate ID list is saved in a short-lived search session (`search_sessions`, TTL 15 minutes).
2. The cursor token is an opaque Base64-encoded payload containing:
   $$\text{cursor} = \text{base64}\left(\text{session\_id} \mathbin{\Vert} \text{offset} \mathbin{\Vert} \text{timestamp}\right)$$
3. Subsequent page fetches retrieve the next slice from the stable session candidate list.
4. Guarantees **zero duplicate cards** and **zero dropped products** during active shopper pagination.
