from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_str: str) -> SemanticVersion:
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str.strip())
        if not match:
            raise ValueError(f"Invalid semantic version format: '{version_str}' (expected 'MAJOR.MINOR.PATCH')")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
        )

    def is_compatible_with(self, other: SemanticVersion) -> bool:
        """A registry version is backward-compatible with a product version if

        they share the same major version and registry minor >= product minor.
        """
        if self.major != other.major:
            return False
        if self.minor < other.minor:
            return False
        return True

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: SemanticVersion) -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)


@dataclass
class DeprecationRecord:
    item_type: str  # category | garment_type | attribute | value
    item_id: str
    deprecated_in: str
    effective_sunset: str
    replacement_id: str | None = None
    reason: str | None = None


class TaxonomyVersionManager:
    """Manages semantic version checks, deprecation lifecycle, and compatibility policies."""

    def __init__(self, active_version: str = "1.0.0") -> None:
        self.active_version = SemanticVersion.parse(active_version)
        self._deprecations: dict[tuple[str, str], DeprecationRecord] = {}

    def is_product_version_supported(self, product_version_str: str) -> bool:
        try:
            prod_ver = SemanticVersion.parse(product_version_str)
            return self.active_version.is_compatible_with(prod_ver)
        except ValueError:
            return False

    def register_deprecation(
        self,
        item_type: str,
        item_id: str,
        deprecated_in: str,
        effective_sunset: str,
        replacement_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        key = (item_type, item_id)
        self._deprecations[key] = DeprecationRecord(
            item_type=item_type,
            item_id=item_id,
            deprecated_in=deprecated_in,
            effective_sunset=effective_sunset,
            replacement_id=replacement_id,
            reason=reason,
        )

    def get_deprecation(self, item_type: str, item_id: str) -> DeprecationRecord | None:
        return self._deprecations.get((item_type, item_id))

    def is_deprecated(self, item_type: str, item_id: str) -> bool:
        return (item_type, item_id) in self._deprecations
