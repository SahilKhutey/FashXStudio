# ARC-08: 05 — Theme Preset Architecture

## 1. Initial Theme Catalogue
ModularMenu ships with 6 platform-curated theme presets:
1. **Minimal (`theme-minimal`)**: Whitespace-forward, clean sans-serif typography, restrained monochrome palette with blue accents.
2. **Luxury (`theme-luxury`)**: Deep obsidian surfaces (`#121212`), refined gold accents (`#d4af37`), and editorial serif typography (Playfair Display / Lora).
3. **Rustic (`theme-rustic`)**: Warm earth tones (`#8b4513`), natural textures, and organic typography (Merriweather).
4. **Contemporary (`theme-contemporary`)**: High visual structure, punchy slate and cyan accents, modern geometric typography (Outfit).
5. **Vibrant (`theme-vibrant`)**: Energetic citrus and coral accents (`#ea580c`), playful curves, and bold titles.
6. **Editorial (`theme-editorial`)**: Magazine-style storytelling, spacious layout, and elegant classical titles (Cinzel / Lora).

## 2. Theme Lifecycle
- `active`: Fully available for new menu selections.
- `deprecated`: Supported for existing menus, but discouraged for new menus.
- `retired`: Ineligible for new menu selections; existing published menus continue rendering safely.
