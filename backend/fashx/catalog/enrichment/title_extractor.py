from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedMatch:
    attribute_id: str
    value: str
    matched_text: str
    start: int
    end: int
    confidence: float = 0.95


# Rules ordered from most specific to general
GARMENT_TYPE_RULES: list[tuple[str, str, float]] = [
    (r"\bpolo\s+shirts?\b|\bpolo\b", "polo_shirt", 0.98),
    (r"\bt[\s-]?shirts?\b|\btees?\b", "t_shirt", 0.99),
    (r"\bcasual\s+shirts?\b", "casual_shirt", 0.98),
    (r"\bformal\s+shirts?\b", "formal_shirt", 0.98),
    (r"\bkurtas?\b", "kurta", 0.99),
    (r"\bkurtis?\b", "kurti", 0.99),
    (r"\bjeans?\b", "jeans", 0.99),
    (r"\btrousers?\b|\bpants?\b|\bchinos?\b", "trousers", 0.96),
    (r"\bshirts?\b", "shirt", 0.95),
    (r"\bdresses?\b|\bgowns?\b", "dress", 0.96),
    (r"\bsneakers?\b|\btrainers?\b", "sneakers", 0.98),
    (r"\bhandbags?\b|\btote\s+bags?\b", "handbag", 0.98),
]

AUDIENCE_RULES: list[tuple[str, str, float]] = [
    (r"\bmen['’]?s?\b|\bgents\b|\bmale\b", "men", 0.98),
    (r"\bwomen['’]?s?\b|\bladies\b|\bfemale\b", "women", 0.98),
    (r"\bboys?\b", "boys", 0.97),
    (r"\bgirls?\b", "girls", 0.97),
    (r"\bunisex\b", "unisex", 0.98),
]

FIT_RULES: list[tuple[str, str, float]] = [
    (r"\boversized?\b", "oversized", 0.97),
    (r"\bslim\s+fit\b|\bslim\b", "slim", 0.96),
    (r"\bregular\s+fit\b|\bregular\b", "regular", 0.95),
    (r"\brelaxed\s+fit\b|\brelaxed\b", "relaxed", 0.96),
    (r"\bloose\s+fit\b|\bloose\b", "loose", 0.95),
    (r"\bskinny\s+fit\b|\bskinny\b", "skinny", 0.96),
    (r"\bwide[- ]leg\b", "wide_leg", 0.97),
]

COLOR_RULES: list[tuple[str, str, float]] = [
    (r"\bnavy(?:\s+blue)?\b", "navy", 0.98),
    (r"\boff[- ]white\b", "off_white", 0.98),
    (r"\brani\s+pink\b", "pink", 0.98),
    (r"\bbottle\s+green\b", "green", 0.98),
    (r"\bolive(?:\s+green)?\b", "olive", 0.97),
    (r"\bblack\b", "black", 0.99),
    (r"\bwhite\b", "white", 0.98),
    (r"\bblue\b", "blue", 0.95),
    (r"\bred\b", "red", 0.97),
    (r"\bgreen\b", "green", 0.96),
    (r"\byellow\b|\bmustard\b", "yellow", 0.96),
    (r"\bpink\b", "pink", 0.96),
    (r"\bmaroon\b|\bwine\b|\bburgundy\b", "burgundy", 0.96),
    (r"\bgrey\b|\bgray\b|\bcharcoal\b", "grey", 0.96),
    (r"\bbeige\b|\bcream\b|\bkhaki\b", "beige", 0.95),
    (r"\bmulti[- ]?colou?red?\b|\bmulticolor\b", "multicolor", 0.96),
]

PATTERN_RULES: list[tuple[str, str, float]] = [
    (r"\bgraphic(?:\s+print)?\b", "graphic", 0.95),
    (r"\bfloral(?:\s+print)?\b", "floral", 0.97),
    (r"\bcheck(?:ed|s)?\b|\bplaid\b|\bgingham\b", "checked", 0.96),
    (r"\bstrip(?:ed|es)?\b", "striped", 0.96),
    (r"\bbandhani\b", "bandhani", 0.98),
    (r"\bblock[- ]print(?:ed)?\b", "block_print", 0.97),
    (r"\bchikankari\b", "chikankari", 0.98),
    (r"\bsolid(?:\s+colou?r)?\b|\bplain\b", "solid", 0.95),
    (r"\bprint(?:ed)?\b", "printed", 0.92),
]

# Note: Fabric rules here detect terms mentioned in title, but NEVER infer percentages.
# "Cotton Blend" -> fabric_blend = "cotton_blend"
# "100% Cotton" or "Cotton" -> fabric = "cotton"
FABRIC_RULES: list[tuple[str, str, str, float]] = [
    (r"\bcotton[- ]poly(?:ester)?[- ]blend\b|\bcotton[- ]blend\b", "fabric_blend", "cotton_blend", 0.96),
    (r"\bsilk[- ]blend\b", "fabric_blend", "silk_blend", 0.96),
    (r"\b100%\s*cotton\b", "fabric", "cotton", 0.98),
    (r"\bcotton\b", "fabric", "cotton", 0.95),
    (r"\blinen\b", "fabric", "linen", 0.96),
    (r"\bdenim\b", "fabric", "denim", 0.97),
    (r"\bsilk\b", "fabric", "silk", 0.95),
    (r"\bpolyester\b", "fabric", "polyester", 0.95),
    (r"\bwool\b", "fabric", "wool", 0.95),
]

SLEEVE_RULES: list[tuple[str, str, float]] = [
    (r"\bsleeveless\b", "sleeveless", 0.98),
    (r"\bshort\s+sleeves?\b|\bhalf\s+sleeves?\b", "short_sleeve", 0.96),
    (r"\blong\s+sleeves?\b|\bfull\s+sleeves?\b", "long_sleeve", 0.96),
    (r"\bthree[- ]quarter\s+sleeves?\b|\b3/4\s+sleeves?\b", "three_quarter_sleeve", 0.96),
]

NECKLINE_RULES: list[tuple[str, str, float]] = [
    (r"\bround\s+neck\b|\bcrew\s*neck\b", "round_neck", 0.97),
    (r"\bv[- ]neck\b", "v_neck", 0.97),
    (r"\bpolo\s+collar\b", "polo_collar", 0.98),
    (r"\bmandarin(?:\s+collar)?\b|\bband\s+collar\b", "mandarin_collar", 0.97),
    (r"\bbutton[- ]down(?:\s+collar)?\b", "button_down", 0.97),
]

OCCASION_RULES: list[tuple[str, str, float]] = [
    (r"\bcasual\b", "casual", 0.90),
    (r"\bformal\b|\boffice\s+wear\b|\bbusiness\b", "formal", 0.90),
    (r"\bfestive\b|\bwedding\b", "festive", 0.92),
    (r"\bparty(?:\s+wear)?\b", "party", 0.88),
    (r"\bsports?\b|\bgym\b|\brunning\b", "sports", 0.92),
    (r"\beveryday\b|\bdaily\s+wear\b", "everyday", 0.86),
]


def extract_title_attributes(title: str) -> list[ExtractedMatch]:
    """Deterministically extract fashion attributes from product title with precise offsets."""
    if not title or not title.strip():
        return []

    matches: list[ExtractedMatch] = []
    occupied_spans: list[tuple[int, int]] = []

    def is_overlapping(start: int, end: int) -> bool:
        return any(start < s_end and end > s_start for s_start, s_end in occupied_spans)

    # 1. Garment type
    for pattern, val, conf in GARMENT_TYPE_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("garment_type", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "garment_type" for match in matches):
            break

    # 2. Intended audience
    for pattern, val, conf in AUDIENCE_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("intended_audience", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "intended_audience" for match in matches):
            break

    # 3. Fit type
    for pattern, val, conf in FIT_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("fit_type", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "fit_type" for match in matches):
            break

    # 4. Color
    for pattern, val, conf in COLOR_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("color", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "color" for match in matches):
            break

    # 5. Pattern
    for pattern, val, conf in PATTERN_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("pattern", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "pattern" for match in matches):
            break

    # 6. Fabric / Material
    for pattern, attr_id, val, conf in FABRIC_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch(attr_id, val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id in {"fabric", "fabric_blend"} for match in matches):
            break

    # 7. Sleeve type
    for pattern, val, conf in SLEEVE_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("sleeve_type", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "sleeve_type" for match in matches):
            break

    # 8. Neckline
    for pattern, val, conf in NECKLINE_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("neckline", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "neckline" for match in matches):
            break

    # 9. Occasion
    for pattern, val, conf in OCCASION_RULES:
        for m in re.finditer(pattern, title, re.IGNORECASE):
            s, e = m.span()
            if not is_overlapping(s, e):
                matches.append(ExtractedMatch("occasion", val, m.group(0), s, e, conf))
                occupied_spans.append((s, e))
                break
        if any(match.attribute_id == "occasion" for match in matches):
            break

    return matches
