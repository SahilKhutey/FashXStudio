from __future__ import annotations

from uuid import UUID

from api.app.core.errors import NotFoundError
from api.app.core.transactions import transaction
from api.app.profile.repositories.intelligence import ProfileIntelligenceRepository
from database.models.identity import UserPhoto


class ProfileIntelligenceApplicationService:
    def __init__(self, repository: ProfileIntelligenceRepository) -> None:
        self.repository = repository

    async def readiness(self, user_id: UUID) -> dict:
        async with transaction(self.repository.session):
            body, _ = await self.repository.current_profile_rows(user_id)
            photo = await self.repository.latest_tryon_photo(user_id)
            skin = await self.repository.latest_skin_tone(user_id)
            body_complete = bool(body and body.height_cm and body.weight_kg and body.build)
            photo_ready = bool(photo and photo.status == "accepted" and photo.ready_for_tryon)
            skin_ready = bool(skin and skin.status == "completed" and skin.confidence >= 0.5)
            missing: list[str] = []
            if not body_complete:
                missing.append("body_profile")
            if not photo_ready:
                missing.append("tryon_reference_photo")
            if not skin_ready:
                missing.append("skin_tone")
            return {
                "profile_version": body.version if body else 0,
                "body_profile_complete": body_complete,
                "tryon_photo_ready": photo_ready,
                "skin_tone_ready": skin_ready,
                "ready_for_tryon": body_complete and photo_ready,
                "missing": missing,
            }

    async def derived(self, user_id: UUID, style_vector: list[float] | None, preferences: dict) -> dict:
        async with transaction(self.repository.session):
            body, _ = await self.repository.current_profile_rows(user_id)
            skin = await self.repository.latest_skin_tone(user_id)
            photo = await self.repository.latest_tryon_photo(user_id)
            body_complete = bool(body and body.height_cm and body.weight_kg and body.build)
            photo_ready = bool(photo and photo.status == "accepted" and photo.ready_for_tryon)
            return {
                "skin_tone_class": skin.tone_class if skin else None,
                "skin_tone_ita": skin.ita_degrees if skin else None,
                "skin_tone_confidence": skin.confidence if skin else None,
                "style_vector": style_vector,
                "profile_version": body.version if body else 0,
                "ready_for_tryon": body_complete and photo_ready,
                "preferences": preferences,
            }

    async def snapshot(self, user_id: UUID, *, tryon_photo_id: UUID | None = None):
        async with transaction(self.repository.session):
            body, preferences = await self.repository.current_profile_rows(user_id)
            if body is None:
                raise NotFoundError("Body profile not found")
            skin = await self.repository.latest_skin_tone(user_id)
            photo = await self.repository.latest_tryon_photo(user_id) if tryon_photo_id is None else await self.repository.session.get(
                UserPhoto, tryon_photo_id
            )
            selected_photo_id = tryon_photo_id or (photo.id if photo else None)
            artifact = await self.repository.create_artifact(
                user_id=user_id,
                version=await self.repository.next_artifact_version(user_id),
                body_snapshot={"height_cm": body.height_cm, "weight_kg": body.weight_kg, "build": body.build},
                preferences_snapshot={
                    "colors_favored": getattr(preferences, "colors_favored", []),
                    "colors_avoided": getattr(preferences, "colors_avoided", []),
                    "categories": getattr(preferences, "categories", []),
                    "budget_min": getattr(preferences, "budget_min", None),
                    "budget_max": getattr(preferences, "budget_max", None),
                },
                tryon_photo_id=selected_photo_id,
                skin_tone_result_id=skin.id if skin else None,
                ready_for_tryon=bool(
                    body.height_cm and body.weight_kg and body.build
                    and photo and photo.status == "accepted" and photo.ready_for_tryon
                ),
            )
            return artifact, skin
