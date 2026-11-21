import copy
from uuid import UUID, uuid4

from app.modules.customization.domain.entities import CustomizationDraft, CustomizationRevision
from app.modules.customization.domain.exceptions import TenantAccessDeniedError


class CustomizationRepository:
    def __init__(self) -> None:
        self._drafts: dict[tuple[str, str], CustomizationDraft] = {}  # (org_id, menu_id) -> draft
        self._menu_org_owner: dict[str, str] = {}  # menu_id -> org_id (ensuring 1 menu belongs to 1 org)
        self._revisions: dict[tuple[str, str, int], CustomizationRevision] = {}  # (org_id, menu_id, rev) -> revision

    def get_customization(self, organization_id: UUID, menu_id: str) -> CustomizationDraft | None:
        org_str = str(organization_id)
        # Check cross-tenant ownership
        owner_org = self._menu_org_owner.get(menu_id)
        if owner_org is not None and owner_org != org_str:
            raise TenantAccessDeniedError(actor_org_id=org_str, target_org_id=owner_org)

        key = (org_str, menu_id)
        draft = self._drafts.get(key)
        return copy.deepcopy(draft) if draft else None

    def save_customization(self, draft: CustomizationDraft) -> CustomizationDraft:
        org_str = str(draft.organization_id)
        owner_org = self._menu_org_owner.get(draft.menu_id)
        if owner_org is not None and owner_org != org_str:
            raise TenantAccessDeniedError(actor_org_id=org_str, target_org_id=owner_org)

        self._menu_org_owner[draft.menu_id] = org_str
        key = (org_str, draft.menu_id)
        self._drafts[key] = copy.deepcopy(draft)

        # Store immutable revision record
        rev_record = CustomizationRevision(
            id=uuid4(),
            customization_id=draft.id,
            organization_id=draft.organization_id,
            menu_id=draft.menu_id,
            revision=draft.revision,
            configuration=copy.deepcopy(draft.configuration),
            created_by=draft.created_by,
            created_at=draft.updated_at,
        )
        self._revisions[(org_str, draft.menu_id, draft.revision)] = rev_record
        return copy.deepcopy(draft)

    def list_revisions(self, organization_id: UUID, menu_id: str) -> list[CustomizationRevision]:
        org_str = str(organization_id)
        owner_org = self._menu_org_owner.get(menu_id)
        if owner_org is not None and owner_org != org_str:
            raise TenantAccessDeniedError(actor_org_id=org_str, target_org_id=owner_org)

        results = [
            copy.deepcopy(r)
            for (o, m, _), r in self._revisions.items()
            if o == org_str and m == menu_id
        ]
        results.sort(key=lambda r: r.revision, reverse=True)
        return results

    def get_revision(
        self, organization_id: UUID, menu_id: str, revision: int
    ) -> CustomizationRevision | None:
        org_str = str(organization_id)
        owner_org = self._menu_org_owner.get(menu_id)
        if owner_org is not None and owner_org != org_str:
            raise TenantAccessDeniedError(actor_org_id=org_str, target_org_id=owner_org)

        key = (org_str, menu_id, revision)
        rev = self._revisions.get(key)
        return copy.deepcopy(rev) if rev else None


_DEFAULT_REPOSITORY = CustomizationRepository()


def get_customization_repository() -> CustomizationRepository:
    return _DEFAULT_REPOSITORY
