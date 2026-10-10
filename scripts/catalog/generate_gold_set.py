"""Generate stratified 200-item gold evaluation dataset for VLM benchmark scoring."""

import csv
import pathlib

GOLD_DIR = pathlib.Path("gold")
GOLD_DIR.mkdir(parents=True, exist_ok=True)
GOLD_CSV = GOLD_DIR / "gold_labels.csv"

# Stratified template archetypes
ARCHETYPES = [
    # Ethnic Tops (Kurtas) - 30 items
    ("Handblock Print Cotton Short Kurta", "Indigo breathable cotton short kurta with mandarin collar", "top", "kurta", "blue", "printed", "full", "crop", "regular", True, "kurta", 2, "ghost_mannequin", True),
    ("Tussar Silk Embroidered Long Kurta", "Mustard yellow festive silk kurta with fine zari work", "top", "kurta", "yellow", "embroidered", "full", "knee", "regular", True, "kurta", 4, "on_model", True),
    ("Khadi Cotton Daily Wear Kurta", "Olive green casual handspun kurta with side pockets", "top", "kurta", "green", "solid", "full", "knee", "relaxed", True, "kurta", 2, "flat_lay", True),
    ("Chanderi Silk Mandarin Kurti", "Maroon traditional kurti with delicate gold piping", "top", "kurta", "red", "solid", "three_quarter", "crop", "slim", True, "kurta", 4, "on_model", True),
    ("Floral Block Print Anarkali Kurta", "Pink calf-length flared floral cotton kurta", "top", "kurta", "pink", "floral", "three_quarter", "midi", "relaxed", True, "kurta", 3, "on_model", True),
    ("Linen Blend Casual Kurta", "Off-white lightweight summer kurta with wooden buttons", "top", "kurta", "white", "solid", "short", "regular", "relaxed", True, "kurta", 2, "ghost_mannequin", True),

    # Western Tops (Shirts, Tees) - 30 items
    ("Classic Oxford Cotton Formal Shirt", "White crisp cotton button-down long sleeve formal shirt", "top", "shirt", "white", "solid", "full", "regular", "slim", False, None, 4, "on_model", True),
    ("Striped Linen Casual Shirt", "Blue and white breathable vertical striped casual shirt", "top", "shirt", "blue", "striped", "short", "regular", "relaxed", False, None, 2, "ghost_mannequin", True),
    ("Checkered Flannel Button-Down Shirt", "Red and black warm plaid flannel winter shirt", "top", "shirt", "red", "checked", "full", "regular", "regular", False, None, 2, "flat_lay", True),
    ("Pima Cotton Crew Neck T-Shirt", "Black premium solid crewneck short sleeve casual tee", "top", "shirt", "black", "solid", "short", "regular", "regular", False, None, 1, "on_model", True),
    ("Floral Print Cuban Collar Shirt", "Mustard resort wear lightweight rayon printed shirt", "top", "shirt", "yellow", "floral", "short", "regular", "relaxed", False, None, 2, "on_model", True),

    # Bottoms (Trousers, Chinos, Jeans) - 40 items
    ("Slim Fit Stretch Cotton Chinos", "Navy blue versatile casual tailored chinos trousers", "bottom", "trousers", "blue", "solid", None, "regular", "slim", False, None, 3, "on_model", True),
    ("Pleated Formal Wool Blend Trousers", "Charcoal grey office formal dress pants", "bottom", "trousers", "black", "solid", None, "regular", "regular", False, None, 4, "on_model", True),
    ("Relaxed Fit Linen Drawstring Trousers", "Beige breathable beach and lounge linen pants", "bottom", "trousers", "beige", "solid", None, "regular", "relaxed", False, None, 2, "ghost_mannequin", True),
    ("Classic Straight Raw Denim Jeans", "Deep indigo sturdy selvedge five-pocket denim jeans", "bottom", "trousers", "blue", "solid", None, "regular", "regular", False, None, 2, "flat_lay", True),
    ("Tapered Khaki Utility Cargo Pants", "Olive green rugged cotton multi-pocket cargo pants", "bottom", "trousers", "green", "solid", None, "regular", "relaxed", False, None, 2, "on_model", True),

    # One-Pieces Ethnic (Sarees, Lehengas, Salwar Sets) - 30 items
    ("Banarasi Katan Silk Saree", "Crimson red handwoven bridal saree with rich gold zari pallu", "one_piece", "saree", "red", "embroidered", None, "maxi", "regular", True, "saree", 5, "on_model", False),
    ("Chanderi Floral Printed Saree", "Teal blue lightweight festive saree with printed motifs", "one_piece", "saree", "blue", "printed", None, "maxi", "regular", True, "saree", 4, "on_model", False),
    ("Velvet Embroidered Bridal Lehenga", "Maroon heavy bridal lehenga choli with ornate embroidery", "one_piece", "lehenga", "red", "embroidered", "short", "maxi", "regular", True, "lehenga", 5, "on_model", False),
    ("Chikankari Georgette Anarkali Salwar Set", "Pastel yellow lucknowi chikan embroidered salwar kameez set", "one_piece", "salwar_set", "yellow", "embroidered", "full", "maxi", "relaxed", True, "salwar_set", 4, "on_model", True),
    ("Bandhani Silk Festive Saree", "Yellow and red traditional tie-dye festive silk saree", "one_piece", "saree", "yellow", "printed", None, "maxi", "regular", True, "saree", 4, "ghost_mannequin", False),

    # One-Pieces Western (Dresses) - 10 items
    ("Floral Tiered Cotton Midi Dress", "Green summer A-line midi dress with puff sleeves", "one_piece", "dress", "green", "floral", "short", "midi", "regular", False, None, 3, "on_model", True),
    ("Solid Ribbed Knit Bodycon Dress", "Black elegant dinner evening party dress", "one_piece", "dress", "black", "solid", "sleeveless", "knee", "slim", False, None, 4, "on_model", True),

    # Outerwear (Blazers, Nehru Jackets, Coats) - 30 items
    ("Raw Silk Sleeveless Nehru Jacket", "Mustard yellow traditional ethnic bundi waistcoat jacket", "outerwear", "jacket", "yellow", "solid", "sleeveless", "crop", "slim", True, "nehru_jacket", 4, "on_model", True),
    ("Structured Linen Summer Blazer", "Beige smart casual two-button tailored notch lapel blazer", "outerwear", "jacket", "beige", "solid", "full", "regular", "slim", False, None, 4, "on_model", True),
    ("Classic Wool Single-Breasted Overcoat", "Charcoal black warm tailored winter outerwear coat", "outerwear", "jacket", "black", "solid", "full", "knee", "regular", False, None, 4, "ghost_mannequin", True),

    # Accessories & Footwear (Unsuitable for VTO) - 30 items
    ("Embroidered Velvet Jutti", "Maroon ethnic wedding footwear with leather sole", "footwear", "jutti", "red", "embroidered", None, None, None, True, "jutti", 4, "flat_lay", False),
    ("Ajrakh Print Modal Silk Dupatta", "Indigo blue natural dyed traditional lightweight dupatta scarf", "accessory", "dupatta", "blue", "printed", None, None, None, True, "dupatta", 3, "flat_lay", False),
]

def generate_gold_set(target_count: int = 200) -> None:
    items: list[dict[str, object]] = []
    idx = 1
    while len(items) < target_count:
        for arch in ARCHETYPES:
            if len(items) >= target_count:
                break
            title, desc, cat, sub_cat, col, pat, slv, lgt, fit, eth, eth_type, form, p_type, tryon = arch
            item_id = f"GOLD-{idx:04d}"
            # Add subtle title variations if cycling
            var_num = (idx // len(ARCHETYPES))
            v_title = f"{title} (Vol {var_num+1})" if var_num > 0 else title
            items.append({
                "item_id": item_id,
                "title": v_title,
                "description": desc,
                "category": cat,
                "sub_category": sub_cat,
                "primary_color": col,
                "pattern": pat,
                "sleeve_length": slv or "",
                "length": lgt or "",
                "fit": fit or "",
                "ethnic_wear": eth,
                "ethnic_type": eth_type or "",
                "formality": form,
                "photo_type": p_type,
                "tryon_suitable": tryon,
            })
            idx += 1

    fieldnames = list(items[0].keys())
    with open(GOLD_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

    print(f"Generated {len(items)} stratified gold label items at {GOLD_CSV}.")

if __name__ == "__main__":
    generate_gold_set()
