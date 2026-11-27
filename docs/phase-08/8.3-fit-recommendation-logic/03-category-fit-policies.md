# 03 — Category Fit Policies

## Controlled Release Table (`FIT_POLICY_VERSION = "1.0"`)

| Category | Required Fields | Optional Fields | Supported Bases | Initial Release (`enabled`) |
|---|---|---|---|---|
| `TSHIRTS` | `CHEST` | `SHOULDER`, `BODY_LENGTH`, `SLEEVE_LENGTH` | `BODY` | `True` |
| `SHIRTS` | `CHEST` | `SHOULDER`, `NECK`, `SLEEVE_LENGTH`, `WAIST` | `BODY` | `False` |
| `KURTAS` | `CHEST` | `SHOULDER`, `LENGTH`, `WAIST` | `BODY` | `False` |
| `TOPS` | `BUST` | `SHOULDER`, `WAIST`, `LENGTH` | `BODY` | `False` |
| `TROUSERS` | `WAIST`, `HIP` | `INSEAM`, `RISE` | `BODY` | `False` |
| `JEANS` | `WAIST`, `HIP` | `INSEAM`, `RISE`, `THIGH` | `BODY` | `False` |
| `DRESSES` | `BUST`, `WAIST`, `HIP` | `LENGTH`, `SHOULDER` | `BODY` | `False` |
| `SAREES` | None | None | None | `False` |
| `LEHENGAS` | `WAIST`, `HIP` | `LENGTH` | `BODY` | `False` |

Unregistered categories return `None` from `get_category_fit_policy` and abstain as `UNSUPPORTED_CATEGORY` (`CATEGORY_NOT_VALIDATED`). Missing optional measurements never block a category match when required fields are present and valid.
