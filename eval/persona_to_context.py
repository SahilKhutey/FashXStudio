"""Translate evaluation persona definitions into user context objects for the ranking pipeline."""

import hashlib
from dataclasses import dataclass, field
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid5

import numpy as np
import yaml

ARCHETYPE_STYLES = [
    "minimal",
    "smart_casual",
    "ethnic",
    "festive",
    "streetwear",
    "casual",
    "formal",
    "classic",
    "glam",
    "party",
    "athleisure",
    "sporty",
    "normcore",
    "comfort",
    "relaxed",
]


def style_to_embedding(style_name: str) -> np.ndarray:
    """Generate a deterministic, unit-normalized 512-d embedding vector for a style archetype."""
    seed = int.from_bytes(hashlib.sha256(style_name.encode("utf-8")).digest()[:4], "big")
    rng = np.random.RandomState(seed)
    v = rng.randn(512).astype(np.float32)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


ARCHETYPE_CENTROIDS = [style_to_embedding(s) for s in ARCHETYPE_STYLES]


@dataclass
class PersonaContext:
    id: str
    name: str
    user_id: UUID
    gender: str
    genders: list[str]
    sizes: list[str]
    budget_min: int  # in INR
    budget_max: int  # in INR
    styles: list[str]
    occasion: str
    monk: int
    undertone: str
    body_type: str
    categories: list[str]
    liked_colors: list[str]
    avoided_colors: list[str]
    ethnic_pref: bool
    cold_start: bool
    taste_vector: np.ndarray
    hidden_ids: set[UUID] = field(default_factory=set)
    saved_ids: set[UUID] = field(default_factory=set)
    primary_size: str = "M"

    @property
    def pmin(self) -> int:
        return self.budget_min

    @property
    def pmax(self) -> int:
        return self.budget_max


def persona_to_context(persona: dict[str, Any]) -> PersonaContext:
    """Transform persona dictionary into typed PersonaContext with taste embedding."""
    p_id = persona["id"]
    user_id = uuid5(NAMESPACE_DNS, f"fashx-persona-{p_id}")
    gender = persona.get("gender", "unisex")

    # Map gender to database candidate genders
    if gender == "female":
        genders = ["female", "unisex", "women"]
    elif gender == "male":
        genders = ["male", "unisex", "men"]
    else:
        genders = ["female", "male", "unisex", "women", "men"]

    sizes = list(persona.get("sizes", ["M"]))
    primary_size = sizes[0] if sizes else "M"
    budget = persona.get("budget", [1000, 5000])
    budget_min, budget_max = budget[0], budget[1]
    styles = list(persona.get("styles", []))
    occasion = persona.get("occasion", "casual")
    monk = int(persona.get("monk", 5))

    # Undertone determination from Monk tone scale (1-10)
    if monk <= 3:
        undertone = "cool"
    elif monk in (4, 5):
        undertone = "neutral"
    else:
        undertone = "warm"

    body_type = persona.get("body_type", "regular")
    categories = list(persona.get("categories", []))
    if not categories:
        categories = ["top", "bottom", "one_piece", "outerwear"]

    liked_colors = list(persona.get("liked_colors", []))
    avoided_colors = list(persona.get("avoid_colors", []))
    ethnic_pref = bool(persona.get("ethnic_pref", False))
    cold_start = bool(persona.get("cold_start", False))

    # Taste vector computation (Step 7.14)
    if cold_start or not styles:
        raw_vec = np.mean(ARCHETYPE_CENTROIDS, axis=0)
    else:
        style_vecs = [style_to_embedding(s) for s in styles]
        raw_vec = np.mean(style_vecs, axis=0)

    norm = np.linalg.norm(raw_vec)
    taste_vec = (raw_vec / norm).astype(np.float32) if norm > 0 else raw_vec.astype(np.float32)

    return PersonaContext(
        id=p_id,
        name=persona.get("name", p_id),
        user_id=user_id,
        gender=gender,
        genders=genders,
        sizes=sizes,
        budget_min=budget_min,
        budget_max=budget_max,
        styles=styles,
        occasion=occasion,
        monk=monk,
        undertone=undertone,
        body_type=body_type,
        categories=categories,
        liked_colors=liked_colors,
        avoided_colors=avoided_colors,
        ethnic_pref=ethnic_pref,
        cold_start=cold_start,
        taste_vector=taste_vec,
        primary_size=primary_size,
    )


def load_personas(path: str = "eval/personas.yml") -> list[PersonaContext]:
    """Load all personas from YAML and convert to PersonaContext list."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [persona_to_context(p) for p in data]
