# No-Result Handling Specification

## 1. Principles of Empty Result Sets
A zero-result response should be an informative, helpful shopping experience rather than an unhelpful dead end.

When a query produces 0 matching items, the search API returns:
```json
{
  "search_id": "8f8b8e01-0000-0000-0000-000000000001",
  "query": "black velvet kurta size XXL under 500",
  "items": [],
  "total": 0,
  "suggestions": [
    "Try removing the price filter (under ₹500)",
    "Try searching in a broader category (Kurtas)",
    "Check alternative sizes"
  ],
  "applied_filters": {
    "size": "XXL",
    "max_price": "500.00",
    "currency": "INR"
  },
  "available_facets": {
    "categories": [
      {"id": "apparel_indian_kurta", "name": "Kurtas", "count": 48}
    ]
  }
}
```

---

## 2. Suggestion Generation Rules
1. **Never silently alter shopper filters**: Suggestions are returned as actionable UI options; the backend does not silently drop filters without shopper consent.
2. **Identify Most Restrictive Filter**: If removing `max_price` yields 45 items, suggest relaxing the price filter.
3. **Typo Correction**: If query terms match a synonym or dictionary word within Damerau-Levenshtein distance $\le 2$, suggest the corrected query (e.g., "Did you mean: *black shirt*?").
