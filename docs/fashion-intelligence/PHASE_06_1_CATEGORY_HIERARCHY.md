# Phase 06.1 — Category Hierarchy Specification

## 1. Top-Level Taxonomy Categories

FashXStudio defines 7 canonical top-level categories:

| Category ID | Display Label | Description |
| :--- | :--- | :--- |
| `apparel` | Apparel | Western and everyday garments worn on the body |
| `ethnic_wear` | Indian and ethnic wear | Traditional and regional Indian clothing |
| `footwear` | Footwear | Shoes, sandals, boots and related footwear |
| `accessories` | Accessories | Wearable accessories, bags and jewellery |
| `activewear` | Activewear | Performance and sports apparel |
| `innerwear` | Innerwear | Base layers, undergarments and sleepwear |
| `outerwear` | Outerwear | Jackets, coats, blazers and protective layers |

## 2. Hierarchical Category Tree

```
fashion
|-- apparel
|   |-- tops
|   |   |-- t_shirts (leaf)
|   |   |-- shirts (leaf)
|   |   |-- blouses (leaf)
|   |   |-- tank_tops (leaf)
|   |   `-- casual_tops (leaf)
|   |-- bottoms
|   |   |-- jeans (leaf)
|   |   |-- trousers (leaf)
|   |   |-- shorts (leaf)
|   |   `-- leggings (leaf)
|   |-- dresses (leaf)
|   |-- skirts (leaf)
|   `-- jumpsuits (leaf)
|
|-- ethnic_wear
|   |-- kurtas_and_kurtis (leaf)
|   |-- sarees (leaf)
|   |-- lehengas (leaf)
|   |-- salwar_suits (leaf)
|   |-- dupattas (leaf)
|   `-- dhotis_and_bottoms (leaf)
|
|-- footwear
|   |-- sneakers (leaf)
|   |-- formal_shoes (leaf)
|   |-- sandals (leaf)
|   |-- slippers (leaf)
|   |-- boots (leaf)
|   `-- heels (leaf)
|
|-- accessories
|   |-- bags (leaf)
|   |-- belts (leaf)
|   |-- jewellery (leaf)
|   |-- watches (leaf)
|   |-- scarves (leaf)
|   `-- eyewear (leaf)
|
|-- activewear
|   |-- sports_tops (leaf)
|   |-- sports_bottoms (leaf)
|   |-- sports_bras (leaf)
|   `-- tracksuits (leaf)
|
|-- innerwear
|   |-- underwear (leaf)
|   |-- bras (leaf)
|   |-- vests (leaf)
|   `-- sleepwear (leaf)
|
`-- outerwear
    |-- jackets (leaf)
    |-- coats (leaf)
    |-- blazers (leaf)
    `-- hoodies (leaf)
```

## 3. Garment Type Mappings (Initial Pilot Scope)

- `t_shirt` -> `apparel_tops_t_shirts` (P0)
- `polo_shirt` -> `apparel_tops_t_shirts`, `apparel_tops_shirts` (P0)
- `casual_shirt` -> `apparel_tops_shirts` (P0)
- `formal_shirt` -> `apparel_tops_shirts` (P0)
- `kurta` -> `ethnic_wear_kurtas_and_kurtis` (P1)
- `kurti` -> `ethnic_wear_kurtas_and_kurtis` (P1)
- `short_kurta` -> `ethnic_wear_kurtas_and_kurtis` (P1)
- `blouse` -> `apparel_tops_blouses` (P1)
- `jeans` -> `apparel_bottoms_jeans` (P2)
- `trousers` -> `apparel_bottoms_trousers` (P2)
- `sneakers` -> `footwear_sneakers` (P2)
- `saree` -> `ethnic_wear_sarees` (P3)
- `lehenga` -> `ethnic_wear_lehengas` (P3)
