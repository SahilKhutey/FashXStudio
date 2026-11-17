# Shopper Profile Field Dictionary

| Field Name | Type | Allowed Values / Formats | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | UUID (v4) | Valid UUID | No | Auto (uuid4) | Unique profile aggregate identifier. |
| `user_id` | UUID (v4) | Valid UUID referencing `users.id` | No | Server-derived | Shopper user ID derived from verified JWT. |
| `height_cm` | Decimal (5, 1) | `80.0` to `250.0` cm | Yes | `None` | Stature in centimeters. Non-medical sizing dimension. |
| `weight_kg` | Decimal (5, 1) | `20.0` to `400.0` kg | Yes | `None` | Weight in kilograms. Optional fit attribute. |
| `preferred_size_system` | String (Enum) | `IN`, `US`, `UK`, `EU`, `INTL` | Yes | `None` | Default sizing system for clothing recommendation. |
| `preferred_fit` | String (Enum) | `SLIM`, `REGULAR`, `RELAXED`, `OVERSIZED`, `NO_PREFERENCE` | Yes | `None` | Silhouette and drape preference. |
| `style_preferences` | Array[String] | Array of `StylePreference` enums | No | `[]` | Fashion aesthetics favored by shopper. |
| `preferred_colors` | Array[String] | Array of `ColorPreference` enums | No | `[]` | Preferred palette swatches. |
| `product_categories` | Array[String] | Array of `ProductCategory` enums | No | `[]` | Garment categories favored during discovery. |
| `shopping_preferences` | JSON Object | `ShoppingPreferences` schema | No | `{}` | Nested object for budget, intents, brands, materials. |
| `shopping_preferences.budget` | JSON Object | `{ min: Decimal, max: Decimal, currency: "INR" }` | Yes | `None` | Price boundary filter. Min must be <= Max. |
| `shopping_preferences.shopping_intents` | Array[String] | `EVERYDAY_WEAR`, `WORKWEAR`, etc. | No | `[]` | Life occasions relevant to shopper's wardrobe. |
| `shopping_preferences.preferred_brands` | Array[String] | Array of string brand names | No | `[]` | Favorite brands for ranking prioritization. |
| `shopping_preferences.avoid_materials` | Array[String] | Array of material names | No | `[]` | Fabric types shopper wishes to avoid. |
| `shopping_preferences.sustainability_preference` | String | `NO_PREFERENCE`, `ORGANIC_ONLY`, `RECYCLED_ONLY`, `HIGH_PRIORITY` | Yes | `NO_PREFERENCE` | Preference for eco-conscious production. |
| `category_sizes` | Array[Object] | Array of `CategorySizeItem` | No | `[]` | Overrides per garment category (e.g., TOPS: M). |
| `version` | Integer | Positive integer >= 1 | No | `1` | Optimistic locking counter. |
| `created_at` | Timestamptz | ISO 8601 UTC timestamp | No | `now()` | Timestamp when profile record was initialized. |
| `updated_at` | Timestamptz | ISO 8601 UTC timestamp | No | `now()` | Timestamp of the most recent profile edit. |
