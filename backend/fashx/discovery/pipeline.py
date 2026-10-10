"""Discovery ranking pipeline with deterministic filtering, weighted scoring, constrained MMR, and truthful explanations."""

import functools
import math
import pathlib
from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import numpy as np
import yaml

from eval.persona_to_context import PersonaContext
from fashx.discovery.catalog_data import CatalogGarmentItem, get_catalog_items
from fashx.observability.stages import stage

TEMPLATES = {
    "taste": "Close to the styles you picked",
    "style": "Matches your {styles} style",
    "occasion": "Works for {occasion}",
    "size_fit": "Available in your size ({size})",
    "price": "Within your usual price range",
    "color": "In colours you tend to like",
    "skin_harmony": "A shade that tends to complement your undertone",
    "freshness": "New this week",
}

SISTER_SIZES: dict[str, list[str]] = {
    "XXS": ["XS"],
    "XS": ["XXS", "S"],
    "S": ["XS", "M"],
    "M": ["S", "L"],
    "L": ["M", "XL"],
    "XL": ["L", "XXL"],
    "XXL": ["XL"],
}

DEFAULT_WEIGHTS = {
    "taste": 1.0,
    "style": 0.5,
    "occasion": 0.4,
    "formality": 0.3,
    "color": 0.3,
    "skin_harmony": 0.10,
    "size_fit": 0.4,
    "price": 0.3,
    "freshness": 0.15,
    "popularity": 0.10,
    "tryon": 0.0,
}


@dataclass
class RankedItem:
    id: UUID
    title: str
    brand: str
    source_id: UUID
    source_status: str
    status: str
    in_stock: bool
    price: float
    price_age_hours: float
    sizes_in_stock: list[str]
    gender: str
    age_group: str
    category: str
    sub_category: str
    image_url: str = ""
    score: float = 0.0
    reasons: list[tuple[str, str]] = field(default_factory=list)
    relaxed: dict[str, bool] = field(default_factory=dict)
    relaxation_tier: int = 0
    features: dict[str, float] = field(default_factory=dict)
    embedding: np.ndarray | None = None


@functools.lru_cache
def load_weights_config(ranker_version: str = "v1") -> tuple[dict[str, float], dict[str, Any]]:
    """Load ranking weights and MMR parameters from versioned YAML config."""
    config_path = pathlib.Path(f"backend/fashx/discovery/weights/{ranker_version}.yml")
    if not config_path.exists():
        # Fallback to default v1 weights
        return DEFAULT_WEIGHTS.copy(), {"lambda": 0.7, "max_per_brand": 3, "max_source_share": 0.6}

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    weights = data.get("weights", DEFAULT_WEIGHTS.copy())
    mmr = data.get("mmr", {"lambda": 0.7, "max_per_brand": 3, "max_source_share": 0.6})
    return weights, mmr


def explain(
    contrib: dict[str, float],
    feats: dict[str, float],
    ctx: PersonaContext,
    *,
    max_reasons: int = 2,
    min_contrib: float = 0.05,
    min_feat: float = 0.6,
) -> list[tuple[str, str]]:
    """Generate truthful justifications from actual contributing features (Step 7.22)."""
    ranked = sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)
    out: list[tuple[str, str]] = []
    for k, c in ranked:
        if k in TEMPLATES and c >= min_contrib and feats.get(k, 0.0) >= min_feat:
            styles_str = ", ".join(ctx.styles[:2]) if ctx.styles else "versatile"
            out.append((
                k,
                TEMPLATES[k].format(
                    styles=styles_str,
                    occasion=ctx.occasion,
                    size=ctx.primary_size,
                )
            ))
        if len(out) == max_reasons:
            break
    return out or [("taste", TEMPLATES["taste"])]


def mmr_select(
    emb: np.ndarray,
    rel: np.ndarray,
    brand: list[str],
    source: list[str],
    sub_categories: list[str] | None = None,
    k: int = 40,
    lam: float = 0.7,
    max_per_brand: int = 3,
    max_source_share: float = 0.6,
    max_per_subcat: int = 3,
) -> list[int]:
    """Maximal Marginal Relevance selection with hard brand/source/category diversity caps (Step 7.21)."""
    n = len(rel)
    if n == 0:
        return []
    chosen: list[int] = []
    maxsim = np.full(n, -1.0)
    cb: Counter[str] = Counter()
    cs: Counter[str] = Counter()
    c_sub: Counter[str] = Counter()
    cap_s = max(1, int(max_source_share * k))

    while len(chosen) < min(k, n):
        s = lam * rel - (1.0 - lam) * np.clip(maxsim, 0.0, None)
        s[chosen] = -np.inf
        for j in range(n):
            if cb[brand[j]] >= max_per_brand or cs[source[j]] >= cap_s or (sub_categories and c_sub[sub_categories[j]] >= max_per_subcat):
                s[j] = -np.inf
        j = int(np.argmax(s))
        if not np.isfinite(s[j]):
            # Constraints infeasible (e.g. single brand or small source pool): relax them
            max_per_brand += 1
            cap_s += 1
            max_per_subcat += 1
            if max_per_brand > k:
                # Add remaining items by pure relevance
                unselected = [idx for idx in range(n) if idx not in chosen]
                unselected.sort(key=lambda idx: rel[idx], reverse=True)
                chosen.extend(unselected[: k - len(chosen)])
                break
            continue
        chosen.append(j)
        cb[brand[j]] += 1
        cs[source[j]] += 1
        if sub_categories:
            c_sub[sub_categories[j]] += 1
        maxsim = np.maximum(maxsim, emb @ emb[j])

    return chosen


def compute_features(item: CatalogGarmentItem, ctx: PersonaContext) -> dict[str, float]:
    """Compute 11 normalized features in [0, 1] for a candidate garment (Step 7.20)."""
    # 1. Taste: Cosine similarity with user taste embedding
    cos_sim = float(np.dot(ctx.taste_vector, item.embedding))
    taste = float(np.clip((cos_sim + 1.0) / 2.0, 0.0, 1.0))

    # 2. Style: Jaccard overlap between persona styles and garment styles
    if ctx.styles and item.styles:
        s_user = {s.lower() for s in ctx.styles}
        s_item = {s.lower() for s in item.styles}
        style = len(s_user & s_item) / len(s_user | s_item)
    else:
        style = 0.5  # Neutral for cold start

    # 3. Occasion: Exact match or neutral
    if not ctx.occasion:
        occasion = 0.5
    elif ctx.occasion.lower() == item.occasion.lower():
        occasion = 1.0
    else:
        occasion = 0.0

    # 4. Formality: Closeness to target formality (assumed 3 for casual, 4 for work/wedding)
    target_formality = 4 if ctx.occasion in ("work", "wedding", "festival") else 2
    formality = 1.0 - abs(target_formality - item.formality) / 4.0

    # 5. Color: Liked colors get 1.0, avoided colors get 0.0, neutral gets 0.5
    col = item.dominant_color.lower()
    if any(c.lower() in col for c in ctx.liked_colors):
        color = 1.0
    elif any(c.lower() in col for c in ctx.avoided_colors):
        color = 0.0
    else:
        color = 0.5

    # 6. Skin harmony: Soft prior based on undertone
    if ctx.undertone == "warm" and col in ("yellow", "red", "gold", "orange", "brown", "beige"):
        skin_harmony = 0.85
    elif ctx.undertone == "cool" and col in ("blue", "white", "black", "pink", "grey", "silver"):
        skin_harmony = 0.85
    else:
        skin_harmony = 0.5

    # 7. Size fit: 1.0 if primary size in stock, 0.7 if sister size, 0.0 otherwise
    if ctx.primary_size and ctx.primary_size in item.sizes_in_stock:
        size_fit = 1.0
    elif any(s in item.sizes_in_stock for s in SISTER_SIZES.get(ctx.primary_size, [])):
        size_fit = 0.7
    elif any(s in item.sizes_in_stock for s in ctx.sizes):
        size_fit = 0.9
    else:
        size_fit = 0.0

    # 8. Price affinity: Closeness to budget midpoint
    budget_mid = (ctx.budget_min + ctx.budget_max) / 2.0
    log_diff = abs(math.log(max(item.price, 1.0)) - math.log(max(budget_mid, 1.0)))
    price = float(np.exp(-log_diff))

    # 9. Freshness: Price checked within 72h
    freshness = float(np.clip(1.0 - item.price_age_hours / 72.0, 0.0, 1.0))

    # 10. Popularity: Normalized neutral prior
    popularity = 0.5

    # 11. Tryon suitability
    tryon = 1.0 if item.tryon_suitable else 0.0

    return {
        "taste": taste,
        "style": style,
        "occasion": occasion,
        "formality": formality,
        "color": color,
        "skin_harmony": skin_harmony,
        "size_fit": size_fit,
        "price": price,
        "freshness": freshness,
        "popularity": popularity,
        "tryon": tryon,
    }


def rank(
    ctx: PersonaContext,
    page: int = 0,
    limit: int = 20,
    db: Any = None,
    ranker: str = "v1",
) -> list[RankedItem]:
    """Retrieve, filter by hard constraints, score, diversify, and paginate feed results."""
    with stage("retrieval"):
        # 1. Candidate Pool
        pool = get_catalog_items()

        # 2. Hard Invariant Filters (Step 7.7)
        # Rules that MUST NEVER RELAX: source_status, status, in_stock, price_age, kids, gender, exclusions, size
        hard_candidates: list[CatalogGarmentItem] = []
        for it in pool:
            if it.source_status != "cleared":
                continue
            if not (it.status == "active" and it.in_stock):
                continue
            if it.price_age_hours > 72.0:
                continue
            if it.age_group == "kids":
                continue
            if it.gender not in ctx.genders:
                continue
            if it.id in ctx.hidden_ids or it.id in ctx.saved_ids:
                continue
            if not (set(it.sizes_in_stock) & set(ctx.sizes)):
                continue
            hard_candidates.append(it)

        if not hard_candidates:
            return []

        # 3. Soft Constraints & 4-Tier Relaxation Ladder (Step 7.14)
        min_target = 40
        tier = 0
        relaxed_flags: dict[str, bool] = {}

        def filter_candidates(candidates: list[CatalogGarmentItem], b_max: float, req_occasion: bool) -> list[CatalogGarmentItem]:
            filtered = []
            for it in candidates:
                if not (ctx.budget_min <= it.price <= b_max):
                    continue
                if req_occasion and ctx.occasion and it.occasion != ctx.occasion and (it.formality < 3 if ctx.occasion in ("work", "wedding") else False):
                    continue
                filtered.append(it)
            return filtered

        # Tier 0 (strict): exact size, budget cap, occasion match, gender
        surviving = filter_candidates(hard_candidates, float(ctx.budget_max), True)

        # Tier 1: drop occasion filter
        if len(surviving) < min_target:
            tier = 1
            relaxed_flags["occasion"] = True
            surviving = filter_candidates(hard_candidates, float(ctx.budget_max), False)

        # Tier 2: expand budget by +50%
        if len(surviving) < min_target:
            tier = 2
            relaxed_flags["budget"] = True
            surviving = filter_candidates(hard_candidates, float(ctx.budget_max) * 1.5, False)

        # Tier 3: sister size (if configured / available)
        if len(surviving) < min_target:
            sister_sizes = set()
            for s in ctx.sizes:
                sister_sizes.update(SISTER_SIZES.get(s, []))
            all_sizes = set(ctx.sizes) | sister_sizes
            tier_3_hard = [
                it for it in pool
                if it.source_status == "cleared"
                and it.status == "active"
                and it.in_stock
                and it.price_age_hours <= 72.0
                and it.age_group != "kids"
                and it.gender in ctx.genders
                and it.id not in ctx.hidden_ids
                and it.id not in ctx.saved_ids
                and (set(it.sizes_in_stock) & all_sizes)
            ]
            t3 = filter_candidates(tier_3_hard, float(ctx.budget_max) * 1.5, False)
            if len(t3) > len(surviving):
                tier = 3
                relaxed_flags["sister_size"] = True
                surviving = t3

        if not surviving:
            surviving = hard_candidates

    # 4. Scoring
    scored: list[RankedItem] = []

    if ranker == "baseline":
        # Pure Taste-Only Baseline (Step 7.6): retrieve with hard filters, rank strictly by cosine similarity
        with stage("scoring"):
            for it in surviving:
                cos_sim = float(np.dot(ctx.taste_vector, it.embedding))
                scored.append(
                    RankedItem(
                        id=it.id,
                        title=it.title,
                        brand=it.brand,
                        source_id=it.source_id,
                        source_status=it.source_status,
                        status=it.status,
                        in_stock=it.in_stock,
                        price=it.price,
                        price_age_hours=it.price_age_hours,
                        sizes_in_stock=it.sizes_in_stock,
                        gender=it.gender,
                        age_group=it.age_group,
                        category=it.category,
                        sub_category=it.sub_category,
                        image_url=it.image_url,
                        score=cos_sim,
                        reasons=[("taste", TEMPLATES["taste"])],
                        relaxed=relaxed_flags.copy(),
                        relaxation_tier=tier,
                        embedding=it.embedding,
                    )
                )
            scored.sort(key=lambda x: x.score, reverse=True)
    else:
        # Multi-feature scoring + MMR diversification (v1/v2)
        with stage("scoring"):
            weights, mmr_cfg = load_weights_config(ranker)
            emb_matrix = np.array([it.embedding for it in surviving])
            rel_scores = []
            contribs_list = []
            feats_list = []

            for it in surviving:
                f = compute_features(it, ctx)
                feats_list.append(f)
                contrib = {k: weights.get(k, 0.0) * f[k] for k in f}
                contribs_list.append(contrib)
                rel = sum(contrib.values())
                rel_scores.append(rel)

            rel_arr = np.array(rel_scores, dtype=np.float32)
            brands = [it.brand for it in surviving]
            sources = [str(it.source_id) for it in surviving]

            # Cold-start uses higher diversity (lower lambda, Step 7.14)
            lam = 0.5 if ctx.cold_start else mmr_cfg.get("lambda", 0.7)
            sub_cats = [it.sub_category for it in surviving]

        with stage("mmr"):
            selected_indices = mmr_select(
                emb=emb_matrix,
                rel=rel_arr,
                brand=brands,
                source=sources,
                sub_categories=sub_cats,
                k=min(len(surviving), limit),
                lam=lam,
                max_per_brand=mmr_cfg.get("max_per_brand", 3),
                max_source_share=mmr_cfg.get("max_source_share", 0.6),
                max_per_subcat=3,
            )

        with stage("explanation"):
            for idx in selected_indices:
                it = surviving[idx]
                c = contribs_list[idx]
                f = feats_list[idx]
                reasons = explain(c, f, ctx)
                scored.append(
                    RankedItem(
                        id=it.id,
                        title=it.title,
                        brand=it.brand,
                        source_id=it.source_id,
                        source_status=it.source_status,
                        status=it.status,
                        in_stock=it.in_stock,
                        price=it.price,
                        price_age_hours=it.price_age_hours,
                        sizes_in_stock=it.sizes_in_stock,
                        gender=it.gender,
                        age_group=it.age_group,
                        category=it.category,
                        sub_category=it.sub_category,
                        image_url=it.image_url,
                        score=float(rel_arr[idx]),
                        reasons=reasons,
                        relaxed=relaxed_flags.copy(),
                        relaxation_tier=tier,
                        features=f.copy(),
                        embedding=it.embedding,
                    )
                )

    # 5. Pagination
    start = page * limit
    end = start + limit
    return scored[start:end]
