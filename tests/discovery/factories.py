"""Factories for generating randomized persona contexts for discovery invariant tests."""

import random
from uuid import uuid4

import numpy as np

from eval.persona_to_context import (
    ARCHETYPE_STYLES,
    PersonaContext,
    style_to_embedding,
)

GENDERS = ["female", "male", "unisex"]
ALL_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
OCCASIONS = ["casual", "work", "party", "festival", "wedding", "workout"]
BODY_TYPES = ["regular", "hourglass", "athletic", "slim", "tall", "plus_size", "petite"]
COLORS = ["black", "white", "blue", "red", "green", "yellow", "beige", "grey", "pink"]


def random_persona_context(rng: random.Random) -> PersonaContext:
    """Build a PersonaContext with randomized constraints for property and invariant testing."""
    gender = rng.choice(GENDERS)
    if gender == "female":
        genders = ["female", "unisex", "women"]
    elif gender == "male":
        genders = ["male", "unisex", "men"]
    else:
        genders = ["female", "male", "unisex", "women", "men"]

    # Select 1 or 2 sizes
    size_count = rng.choice([1, 2])
    sizes = rng.sample(ALL_SIZES, size_count)
    primary_size = sizes[0]

    b_min = rng.choice([500, 1000, 1500, 2000, 2500])
    b_max = b_min + rng.choice([1500, 2500, 4000, 6000, 10000])

    style_count = rng.choice([1, 2, 3])
    styles = rng.sample(ARCHETYPE_STYLES, style_count)

    occasion = rng.choice(OCCASIONS)
    monk = rng.randint(2, 9)
    if monk <= 3:
        undertone = "cool"
    elif monk in (4, 5):
        undertone = "neutral"
    else:
        undertone = "warm"

    body_type = rng.choice(BODY_TYPES)
    categories = rng.sample(["top", "bottom", "one_piece", "outerwear"], rng.randint(1, 4))

    liked_colors = rng.sample(COLORS, rng.randint(1, 3))
    avoided_colors = rng.sample([c for c in COLORS if c not in liked_colors], rng.randint(0, 2))

    # Some hidden and saved item IDs to test exclusion
    hidden_ids = {uuid4() for _ in range(rng.randint(0, 3))}
    saved_ids = {uuid4() for _ in range(rng.randint(0, 3))}

    # Taste embedding
    style_vecs = [style_to_embedding(s) for s in styles]
    raw_vec = np.mean(style_vecs, axis=0)
    norm = np.linalg.norm(raw_vec)
    taste_vec = (raw_vec / norm).astype(np.float32) if norm > 0 else raw_vec.astype(np.float32)

    return PersonaContext(
        id=f"rand-{rng.randint(1000, 9999)}",
        name="Random Persona",
        user_id=uuid4(),
        gender=gender,
        genders=genders,
        sizes=sizes,
        budget_min=b_min,
        budget_max=b_max,
        styles=styles,
        occasion=occasion,
        monk=monk,
        undertone=undertone,
        body_type=body_type,
        categories=categories,
        liked_colors=liked_colors,
        avoided_colors=avoided_colors,
        ethnic_pref=rng.choice([True, False]),
        cold_start=False,
        taste_vector=taste_vec,
        hidden_ids=hidden_ids,
        saved_ids=saved_ids,
        primary_size=primary_size,
    )
