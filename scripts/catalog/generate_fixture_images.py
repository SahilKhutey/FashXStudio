#!/usr/bin/env python3
"""Generate high-resolution (1024x1024) reproducible fixture images for catalog seed."""

from pathlib import Path

from PIL import Image, ImageDraw

IMAGES_DIR = Path("catalog_seed/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

COLOR_MAP = {
    "teal": ((18, 120, 120), (32, 178, 170)),
    "white": ((235, 235, 240), (250, 250, 255)),
    "maroon": ((110, 15, 30), (145, 25, 45)),
    "navy": ((15, 25, 60), (30, 45, 95)),
    "black": ((25, 25, 28), (45, 45, 50)),
    "pink": ((215, 105, 135), (245, 160, 185)),
    "green": ((45, 105, 55), (70, 140, 85)),
    "yellow": ((215, 165, 20), (245, 200, 45)),
    "beige": ((195, 175, 145), (225, 210, 185)),
    "grey": ((110, 115, 120), (160, 165, 170)),
    "red": ((185, 25, 30), (225, 50, 55)),
    "blue": ((35, 90, 165), (65, 135, 215)),
    "purple": ((90, 35, 115), (130, 65, 165)),
    "orange": ((215, 85, 25), (245, 125, 55)),
}

GARMENTS = [
    ("g001", "teal", "top", "Women's Teal Cotton Printed Kurta", "printed"),
    ("g002", "white", "top", "Men's White Linen Casual Shirt", "solid"),
    ("g003", "maroon", "top", "Women's Maroon Embroidered Anarkali Kurta", "embroidered"),
    ("g004", "navy", "top", "Men's Navy Slim Fit Formal Shirt", "solid"),
    ("g005", "black", "top", "Unisex Black Graphic Streetwear Hoodie", "printed"),
    ("g006", "pink", "top", "Women's Pink Floral Chiffon Blouse", "floral"),
    ("g007", "green", "top", "Men's Olive Green Casual T-Shirt", "solid"),
    ("g008", "yellow", "top", "Women's Yellow Festive Short Kurti", "solid"),
    ("g009", "navy", "bottom", "Men's Dark Navy Slim Fit Denim Jeans", "solid"),
    ("g010", "beige", "bottom", "Women's Beige Wide Leg Palazzo Pants", "solid"),
    ("g011", "grey", "bottom", "Men's Grey Chino Formal Trousers", "solid"),
    ("g012", "black", "bottom", "Women's Black High-Waist Skinny Jeans", "solid"),
    ("g013", "red", "bottom", "Women's Red Printed Cotton Ethnic Skirt", "printed"),
    ("g014", "white", "bottom", "Women's White Cotton Stretch Leggings", "solid"),
    ("g015", "beige", "bottom", "Men's Khaki Casual Cargo Trousers", "solid"),
    ("g016", "blue", "one_piece", "Women's Blue Tiered Maxi Summer Dress", "floral"),
    ("g017", "green", "one_piece", "Women's Emerald Green Festive Kurta Set", "embroidered"),
    ("g018", "purple", "one_piece", "Women's Purple Silk Blend Festive Dress", "solid"),
    ("g019", "orange", "one_piece", "Women's Orange Striped Cotton A-Line Dress", "striped"),
    ("g020", "black", "one_piece", "Women's Black Cocktail Slip Dress", "solid"),
]


def render_garment_image(
    gid: str, color_name: str, category: str, title: str, pattern: str
) -> Path:
    width, height = 1024, 1024
    base_color, highlight_color = COLOR_MAP.get(color_name, ((100, 100, 100), (150, 150, 150)))

    # Studio background: clean off-white gradient
    img = Image.new("RGB", (width, height), (246, 247, 249))
    draw = ImageDraw.Draw(img)

    # Subtle studio spotlight vignette
    for r in range(500, 0, -25):
        alpha = int((1 - (r / 500)) * 25)
        draw.ellipse(
            [512 - r, 480 - r, 512 + r, 480 + r],
            fill=(246 + alpha // 4, 247 + alpha // 4, 249 + alpha // 4),
        )

    # Garment silhouette
    if category == "top":
        # Draw torso / top silhouette
        draw.polygon(
            [
                (512, 180),
                (320, 260),
                (370, 420),
                (430, 390),
                (420, 680),
                (604, 680),
                (594, 390),
                (654, 420),
                (704, 260),
            ],
            fill=base_color,
            outline=(20, 20, 20),
            width=2,
        )
        # Collar / neckline
        draw.polygon([(460, 180), (512, 250), (564, 180)], fill=(240, 240, 242))
    elif category == "bottom":
        # Draw trousers / bottom silhouette
        draw.polygon(
            [(410, 250), (614, 250), (634, 760), (544, 760), (512, 440), (480, 760), (390, 760)],
            fill=base_color,
            outline=(20, 20, 20),
            width=2,
        )
        # Waistband line
        draw.line([(410, 290), (614, 290)], fill=highlight_color, width=4)
    else:  # one_piece
        # Draw dress / one_piece silhouette
        draw.polygon(
            [
                (470, 180),
                (370, 250),
                (410, 370),
                (440, 440),
                (320, 760),
                (704, 760),
                (584, 440),
                (614, 370),
                (654, 250),
                (554, 180),
            ],
            fill=base_color,
            outline=(20, 20, 20),
            width=2,
        )
        # Waist sash / belt line
        draw.line([(440, 440), (584, 440)], fill=highlight_color, width=6)

    # Pattern accents
    if pattern == "striped":
        for y in range(300, 700, 35):
            draw.line([(380, y), (644, y)], fill=highlight_color, width=3)
    elif pattern == "embroidered":
        for px in range(460, 565, 20):
            for py in range(260, 400, 25):
                draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=highlight_color)
    elif pattern == "floral":
        for fx, fy in [(470, 320), (550, 360), (490, 450), (540, 520), (450, 600)]:
            draw.ellipse([fx - 8, fy - 8, fx + 8, fy + 8], fill=highlight_color)
            draw.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=(255, 255, 255))
    elif pattern == "printed":
        for px, py in [(460, 310), (560, 340), (510, 420), (440, 510), (580, 580)]:
            draw.rectangle([px - 6, py - 6, px + 6, py + 6], fill=highlight_color)

    # Studio product card overlay at bottom
    draw.rectangle([(80, 840), (944, 960)], fill=(255, 255, 255), outline=(220, 225, 230), width=2)
    draw.text((110, 860), f"FashXStudio Fixture · {gid.upper()}", fill=(79, 70, 229))
    draw.text((110, 890), title, fill=(17, 24, 39))
    draw.text(
        (110, 920),
        f"Category: {category.title()} | Color: {color_name.title()} | Pattern: {pattern.title()} | Studio Archive",
        fill=(107, 114, 128),
    )

    out_path = IMAGES_DIR / f"{gid}.jpg"
    img.save(out_path, format="JPEG", quality=95)
    return out_path


def main():
    print("Generating 20 1024x1024 catalog fixture images...")
    for gid, color, cat, title, pattern in GARMENTS:
        p = render_garment_image(gid, color, cat, title, pattern)
        print(f"  Created: {p} ({p.stat().st_size} bytes)")
    print("Done. All 20 images generated successfully.")


if __name__ == "__main__":
    main()
