# Phase 06.1 — Indian-Wear Specification

## 1. Context and Objective

Indian wear requires dedicated structured modeling rather than forcing regional garments into Western clothing abstractions. FashXStudio treats Indian ethnic fashion as a first-class citizen in the taxonomy.

## 2. Structured Indian-Wear Attributes

| Field | Data Type | Permitted Values / Description |
| :--- | :--- | :--- |
| `ethnic_garment_type` | `enum` | `kurta`, `kurti`, `short_kurta`, `anarkali_kurta`, `saree`, `lehenga`, `salwar_suit`, `dhoti`, `dupatta` |
| `kurta_length` | `enum` | `short`, `knee`, `calf`, `ankle`, `floor` |
| `kurta_style` | `enum` | `straight`, `a_line`, `anarkali`, `angrakha`, `asymmetric` |
| `saree_drape_style` | `enum` | `nivi`, `bengali`, `gujarati`, `regional_other` |
| `saree_length_meters` | `numeric` | Saree length in meters (typically 5.5m to 6.2m including blouse piece) |
| `blouse_included` | `boolean` | `true`, `false`, `null` (unknown) |
| `dupatta_included` | `boolean` | `true`, `false`, `null` (unknown) |
| `closure_type` | `enum` | `buttons`, `hooks`, `zipper`, `tie_up`, `slip_on` |
| `embellishments` | `list[enum]` | `zari`, `mirror_work`, `sequins`, `beads`, `embroidery`, `gotta_patti`, `thread_work` |
| `craft_technique` | `list[enum]` | `handloom`, `powerloom`, `chikankari`, `block_print`, `bandhani`, `ikat`, `kalamkari`, `kantha`, `phulkari` |
| `weave_type` | `enum` | `handloom`, `powerloom`, `plain_weave`, `twill`, `jacquard`, `brocade`, `chanderi`, `banarasi`, `kanchipuram` |
| `set_components` | `list[enum]` | `kurta`, `bottom`, `dupatta`, `blouse`, `skirt`, `jacket` |

## 3. Example Product Representations

### Kurta Set (P1)
```json
{
  "taxonomy_version": "1.0.0",
  "category_id": "ethnic_wear_kurtas_and_kurtis",
  "garment_type_id": "kurta",
  "style_family": "indian_ethnic",
  "intended_audience": "women",
  "occasions": ["festive", "traditional_ceremony"],
  "indian_wear": {
    "ethnic_garment_type": "kurta",
    "kurta_length": "knee",
    "kurta_style": "straight",
    "closure_type": "buttons",
    "craft_technique": ["chikankari"],
    "embellishments": ["embroidery"],
    "set_components": ["kurta", "bottom", "dupatta"]
  }
}
```

### Handloom Saree (P3)
```json
{
  "taxonomy_version": "1.0.0",
  "category_id": "ethnic_wear_sarees",
  "garment_type_id": "saree",
  "style_family": "indian_ethnic",
  "intended_audience": "women",
  "occasions": ["wedding", "traditional_ceremony"],
  "indian_wear": {
    "ethnic_garment_type": "saree",
    "saree_drape_style": "nivi",
    "saree_length_meters": 6.2,
    "blouse_included": true,
    "craft_technique": ["handloom"],
    "weave_type": "banarasi",
    "embellishments": ["zari"]
  }
}
```
