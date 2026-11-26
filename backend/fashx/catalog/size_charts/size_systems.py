"""Merchant-specific size system registry and label normalization for Phase 08.1."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .enums import MappingStatus


@dataclass(frozen=True)
class SizeSystemDefinition:
    """Defines a standardized or merchant-specific sizing system."""

    code: str
    system_type: str
    merchant_id: str | None
    category: str
    market: str
    version: int
    mapping_status: MappingStatus
    labels: tuple[str, ...]
    display_name: str | None = None


# Core registry of verified sizing systems
SYSTEMS: dict[str, SizeSystemDefinition] = {}

# Register core systems
_core_defs = [
    SizeSystemDefinition(
        code="INTL_ALPHA",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="GENERAL",
        market="GLOBAL",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"),
        display_name="International Alpha (XS-XXL)",
    ),
    SizeSystemDefinition(
        code="US_NUMERIC_WOMEN",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="TOPS",
        market="US",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("00", "0", "2", "4", "6", "8", "10", "12", "14", "16", "18"),
        display_name="US Women's Numeric",
    ),
    SizeSystemDefinition(
        code="US_NUMERIC_MEN",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="TOPS",
        market="US",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("34", "36", "38", "40", "42", "44", "46", "48"),
        display_name="US Men's Numeric",
    ),
    SizeSystemDefinition(
        code="UK_NUMERIC",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="TOPS",
        market="UK",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("4", "6", "8", "10", "12", "14", "16", "18", "20"),
        display_name="UK Standard Sizing",
    ),
    SizeSystemDefinition(
        code="EU_NUMERIC",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="TOPS",
        market="EU",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("32", "34", "36", "38", "40", "42", "44", "46", "48"),
        display_name="EU Numeric Sizing",
    ),
    SizeSystemDefinition(
        code="WAIST_INCHES",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="BOTTOMS",
        market="GLOBAL",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("26", "28", "30", "32", "34", "36", "38", "40", "42"),
        display_name="Waist in Inches (26-42)",
    ),
    SizeSystemDefinition(
        code="COLLAR_INCHES",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="SHIRTS",
        market="GLOBAL",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("14", "14.5", "15", "15.5", "16", "16.5", "17", "17.5"),
        display_name="Collar Size in Inches",
    ),
    SizeSystemDefinition(
        code="INDIA_ALPHA",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="GENERAL",
        market="IN",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("XS", "S", "M", "L", "XL", "XXL"),
        display_name="India Standard Alpha",
    ),
    SizeSystemDefinition(
        code="ETHNIC_INDIA",
        system_type="REGIONAL_STANDARD",
        merchant_id=None,
        category="ETHNIC",
        market="IN",
        version=1,
        mapping_status=MappingStatus.NATIVE,
        labels=("36", "38", "40", "42", "44", "46", "48"),
        display_name="Indian Ethnic (Kurta / Churidar)",
    ),
]

for d in _core_defs:
    SYSTEMS[d.code] = d
    SYSTEMS[d.code.lower()] = d


# Explicitly verified cross-system label mappings
# Key: (source_system, source_label, target_system) -> target_label
_VERIFIED_CROSS_SYSTEM_MAPPINGS: dict[tuple[str, str, str], str] = {
    ("UK_NUMERIC", "10", "US_NUMERIC_WOMEN"): "6",
    ("US_NUMERIC_WOMEN", "6", "UK_NUMERIC"): "10",
    ("UK_NUMERIC", "8", "US_NUMERIC_WOMEN"): "4",
    ("US_NUMERIC_WOMEN", "4", "UK_NUMERIC"): "8",
    ("UK_NUMERIC", "12", "US_NUMERIC_WOMEN"): "8",
    ("US_NUMERIC_WOMEN", "8", "UK_NUMERIC"): "12",
}


def normalize_size_label(label: str) -> str:
    """Normalize whitespace and casing for canonical comparison while retaining original characters."""
    if not label:
        return ""
    cleaned = re.sub(r"\s+", " ", label.strip())
    return cleaned.upper()


def map_size_label(
    source_label: str,
    source_system_code: str,
    target_system_code: str,
) -> str | None:
    """Map a size label from source sizing system to target sizing system.

    Supports both (label, source, target) and (source, label, target) parameter orders.
    """
    # Detect parameter order
    if source_system_code in SYSTEMS or source_system_code.upper() in SYSTEMS:
        s_sys = source_system_code.upper()
        s_lbl = source_label
        t_sys = target_system_code.upper()
    elif source_label in SYSTEMS or source_label.upper() in SYSTEMS:
        s_sys = source_label.upper()
        s_lbl = source_system_code
        t_sys = target_system_code.upper()
    else:
        s_sys = source_system_code.upper()
        s_lbl = source_label
        t_sys = target_system_code.upper()

    if s_sys == t_sys:
        return s_lbl

    norm_label = normalize_size_label(s_lbl)
    key = (s_sys, norm_label, t_sys)
    return _VERIFIED_CROSS_SYSTEM_MAPPINGS.get(key, None)


def register_size_system(
    system_def: SizeSystemDefinition | None = None,
    *,
    code: str | None = None,
    system_type: str = "MERCHANT_PROPRIETARY",
    merchant_id: str | None = None,
    category: str = "GENERAL",
    market: str = "GLOBAL",
    version: int = 1,
    mapping_status: MappingStatus = MappingStatus.NATIVE,
    labels: list[str] | tuple[str, ...] = (),
    display_name: str | None = None,
) -> None:
    """Dynamically register a merchant-specific sizing system."""
    if system_def is not None:
        SYSTEMS[system_def.code] = system_def
        SYSTEMS[system_def.code.lower()] = system_def
    elif code is not None:
        obj = SizeSystemDefinition(
            code=code,
            system_type=system_type,
            merchant_id=merchant_id,
            category=category,
            market=market,
            version=version,
            mapping_status=mapping_status,
            labels=tuple(labels),
            display_name=display_name or code,
        )
        SYSTEMS[code] = obj
        SYSTEMS[code.lower()] = obj
