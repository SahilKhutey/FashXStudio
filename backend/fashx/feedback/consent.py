"""Purpose-specific consent & withdrawal enforcement for Phase 08.5 (Task 8.5.10)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fashx.feedback.enums import ConsentPurpose


@dataclass(frozen=True)
class ConsentRecordEntry:
    shopper_id: str
    purpose: ConsentPurpose
    status: str  # "GRANTED" | "WITHDRAWN"
    policy_version: str
    revision: int
    source: str
    recorded_at: datetime
    withdrawn_at: datetime | None = None


class FeedbackConsentService:
    """Tracks append-only purpose-specific consent and enforces personalization gates."""

    def __init__(self, *, default_essential: bool = True) -> None:
        self._history: dict[tuple[str, ConsentPurpose], list[ConsentRecordEntry]] = {}
        self._default_essential = default_essential

    def set_consent(
        self,
        *,
        shopper_id: str,
        purpose: ConsentPurpose | str,
        granted: bool,
        policy_version: str = "2026.1",
        source: str = "app",
    ) -> ConsentRecordEntry:
        purpose_enum = ConsentPurpose(purpose) if isinstance(purpose, str) else purpose
        key = (shopper_id, purpose_enum)
        hist = self._history.setdefault(key, [])
        rev = len(hist) + 1
        now = datetime.now(UTC)
        entry = ConsentRecordEntry(
            shopper_id=shopper_id,
            purpose=purpose_enum,
            status="GRANTED" if granted else "WITHDRAWN",
            policy_version=policy_version,
            revision=rev,
            source=source,
            recorded_at=now,
            withdrawn_at=None if granted else now,
        )
        hist.append(entry)
        return entry

    def withdraw(
        self,
        *,
        shopper_id: str,
        purpose: ConsentPurpose | str,
        policy_version: str = "2026.1",
        source: str = "app",
    ) -> ConsentRecordEntry:
        return self.set_consent(
            shopper_id=shopper_id,
            purpose=purpose,
            granted=False,
            policy_version=policy_version,
            source=source,
        )

    def get_latest(
        self, shopper_id: str, purpose: ConsentPurpose | str
    ) -> ConsentRecordEntry | None:
        purpose_enum = ConsentPurpose(purpose) if isinstance(purpose, str) else purpose
        hist = self._history.get((shopper_id, purpose_enum), [])
        return hist[-1] if hist else None

    def get_revision(self, shopper_id: str, purpose: ConsentPurpose | str) -> int:
        latest = self.get_latest(shopper_id, purpose)
        return latest.revision if latest else 1

    def has_active_consent(
        self, *, shopper_id: str, purpose: ConsentPurpose | str
    ) -> bool:
        purpose_enum = ConsentPurpose(purpose) if isinstance(purpose, str) else purpose
        latest = self.get_latest(shopper_id, purpose_enum)
        if latest is None:
            return (
                self._default_essential
                and purpose_enum == ConsentPurpose.ESSENTIAL_SERVICE
            )
        return latest.status == "GRANTED"

    def can_collect(
        self,
        *,
        shopper_id: str,
        purpose: ConsentPurpose | str,
        event_type: str | None = None,
    ) -> bool:
        return self.has_active_consent(shopper_id=shopper_id, purpose=purpose)

    def can_process_existing_event(
        self,
        *,
        shopper_id: str,
        purpose: ConsentPurpose | str,
    ) -> bool:
        return self.has_active_consent(shopper_id=shopper_id, purpose=purpose)

    def can_personalize(self, shopper_id: str) -> bool:
        return self.has_active_consent(
            shopper_id=shopper_id, purpose=ConsentPurpose.PERSONALIZED_RANKING
        )

    def list_consents(self, shopper_id: str) -> list[ConsentRecordEntry]:
        out: list[ConsentRecordEntry] = []
        for purpose in ConsentPurpose:
            latest = self.get_latest(shopper_id, purpose)
            if latest is not None:
                out.append(latest)
        return out
