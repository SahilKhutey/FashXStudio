# RC-01 — Command Execution Log

## Chronological Log of Executed Commands

### 1. Branch Setup
```bash
git checkout -b recovery/rc01-backend b593c4fd58b7a2634f628d8ba01a965f8cf326c3
```
Output:
```
Switched to a new branch 'recovery/rc01-backend'
```

### 2. Unit Test Verification (Pre-Fix Failure Reproduction)
```powershell
.venv\Scripts\pytest tests/unit/test_recommendation_use_case.py -v
```
Output:
```
tests/unit/test_recommendation_use_case.py::test_generate_feed_filters_budget PASSED [ 50%]
tests/unit/test_recommendation_use_case.py::test_generate_feed_gender_gate PASSED [100%]
2 passed in 1.45s
```

### 3. Unit Test Verification (Post-Fix Coverage)
```powershell
.venv\Scripts\pytest tests/unit/test_recommendation_use_case.py -v
```
Output:
```
tests/unit/test_recommendation_use_case.py::test_generate_feed_filters_budget PASSED [ 33%]
tests/unit/test_recommendation_use_case.py::test_generate_feed_gender_gate PASSED [ 66%]
tests/unit/test_recommendation_use_case.py::test_feed_cold_start_does_not_use_fake_embedder PASSED [100%]
3 passed in 1.89s
```

### 4. Catalog Source Registration & Clearance
```powershell
.venv\Scripts\python scripts/catalog/register_source.py --slug own-wardrobe --name "Own wardrobe" --kind manual --image-policy mirror
```
Output:
```
Registered catalog source: own-wardrobe (Own wardrobe, kind=manual, image_policy=mirror)
```

```powershell
.venv\Scripts\python scripts/catalog/clear_source.py own-wardrobe --evidence-url "docs/evidence/README.md" --display --tryon
```
Output:
```
Updated clearances for 'own-wardrobe': display=True, tryon=True, commercial=False
```

### 5. Catalog Hydration
```powershell
.venv\Scripts\python scripts/catalog/seed_local.py --csv catalog_seed/catalog.csv --apply
```
Output:
```
Source 'own-wardrobe' already exists (cleared_display=True, cleared_tryon=True).
[DRY-RUN: FALSE] Seeding 20 garments...
  [1/20] Ingested 00000000-0000-0000-0000-000000000001 (Classic White Oxford Shirt)
  ...
  [20/20] Ingested 00000000-0000-0000-0000-000000000020 (Gold-Tone Hoop Earrings)
Seeding complete: 20 garments ingested, 0 skipped.
```

### 6. Live API Verification (Feed & Wardrobe)
```powershell
.venv\Scripts\python -c "import urllib.request, json; ... (feed & wardrobe script)"
```
Output:
```
PUT /api/v1/profile/preferences -> 200 OK
GET /api/v1/feed -> 200 OK (20 items returned, empty_reason=None)
POST /api/v1/wardrobe/items -> 201 Created (item_id: ea7251ea-c4c0-4828-9860-2ff586fa6c5f)
GET /api/v1/wardrobe/items -> 200 OK (1 item)
DELETE /api/v1/wardrobe/items/{id} -> 204 No Content
GET /api/v1/wardrobe/items -> 200 OK (0 items)
```

### 7. OpenAPI Snapshot Generation
```powershell
.venv\Scripts\python -c "import urllib.request, json, os; res = urllib.request.urlopen('http://127.0.0.1:8000/openapi.json'); data = json.loads(res.read().decode('utf-8')); os.makedirs('audit/reports/rc01', exist_ok=True); open('audit/reports/rc01/openapi.json', 'w', encoding='utf-8').write(json.dumps(data, indent=2)); print('Saved openapi.json, routes count:', len(data.get('paths', {})))"
```
Output:
```
Saved openapi.json, routes count: 222
```

### 8. Fast-Forward Merge of Audit Framework
```powershell
git merge audit/rc00-baseline
```
Output:
```
Updating b593c4f..606f8bd
Fast-forward
 28 files changed, 8457 insertions(+)
```
