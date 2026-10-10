"""Hard-rule invariant test verifying 0 violations across 200 random personas x 3 pages (Step 7.7)."""

import random

from fashx.discovery.pipeline import rank
from tests.discovery.factories import random_persona_context


def test_no_hard_rule_violations_across_random_personas(db_with_real_catalog):
    """Verify that no hard constraints are ever violated across 200 personas x 3 pages."""
    rng = random.Random(7)
    for _ in range(200):
        ctx = random_persona_context(rng)
        for page in range(3):
            items = rank(ctx, page=page, db=db_with_real_catalog)
            for it in items:
                assert it.source_status == "cleared", f"Item {it.id} source not cleared"
                assert it.status == "active" and it.in_stock, f"Item {it.id} inactive or out of stock"
                assert it.price_age_hours <= 72, f"Item {it.id} price check > 72h ({it.price_age_hours})"
                assert ctx.budget_min <= it.price <= ctx.budget_max or it.relaxed.get("budget"), (
                    f"Item {it.price} outside budget [{ctx.budget_min}, {ctx.budget_max}] without explicit relaxation"
                )
                assert set(it.sizes_in_stock) & set(ctx.sizes), (
                    f"Item sizes {it.sizes_in_stock} do not overlap persona sizes {ctx.sizes}"
                )
                assert it.gender in ctx.genders, f"Item gender {it.gender} not in allowed {ctx.genders}"
                assert it.id not in ctx.hidden_ids and it.id not in ctx.saved_ids, (
                    f"Item {it.id} was excluded or saved"
                )
                assert it.age_group != "kids", f"Item {it.id} is kids wear"
