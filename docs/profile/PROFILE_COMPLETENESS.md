# Feature-Based Profile Completeness

Rather than presenting an arbitrary completeness score, FashXStudio evaluates profile readiness against discrete product capabilities.

## 1. Feature Readiness Rules

| Feature Key | Required Profile Fields | Product Capability Unlocked |
| :--- | :--- | :--- |
| `product_discovery` | Always ready (`True`) | Basic catalog browsing and search. |
| `personalized_recommendations` | `style_preferences` OR `product_categories` | Curated home feed and tailored style rails. |
| `size_guidance` | `preferred_size_system` OR `category_sizes` | Sizing charts and brand cross-reference conversions. |
| `fit_recommendation` | `height_cm` AND `preferred_fit` | Fit advice (e.g. "Size up for your preferred relaxed drape"). |
| `advanced_vto` | `height_cm` | Stature calibration for virtual try-on models. |

## 2. Completeness Calculation
- `overall_percentage`: Integer from 0 to 100 calculated as:
  $$ \text{overall\_percentage} = \mathrm{round}\left(\frac{\text{ready\_features}}{\text{total\_features}} \times 100\right) $$
- `overall_status`:
  - `COMPLETE`: All 5 features ready (100%).
  - `PARTIAL`: 2 to 4 features ready.
  - `EMPTY`: 0 or 1 feature ready.
