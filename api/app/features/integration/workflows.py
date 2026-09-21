from dataclasses import dataclass
from enum import StrEnum


class WorkflowName(StrEnum):
    ONBOARDING_TO_DISCOVERY = "onboarding_to_discovery"
    SEARCH_TO_PRODUCT = "search_to_product"
    PRODUCT_TO_OUTFIT = "product_to_outfit"
    SHOPPING_TO_COMMERCE = "shopping_to_commerce"
    ENGAGEMENT_TO_PERSONALIZATION = "engagement_to_personalization"


@dataclass(frozen=True)
class WorkflowStep:
    feature_id: str
    action: str
    required: bool = True


WORKFLOWS: dict[WorkflowName, tuple[WorkflowStep, ...]] = {
    WorkflowName.ONBOARDING_TO_DISCOVERY: (
        WorkflowStep("FX-F02", "user_context"),
        WorkflowStep("FX-F12", "regional_context", required=False),
        WorkflowStep("FX-F09", "personalize", required=False),
        WorkflowStep("FX-F03", "discover"),
    ),
    WorkflowName.SEARCH_TO_PRODUCT: (
        WorkflowStep("FX-F04", "search"),
        WorkflowStep("FX-F05", "product_detail"),
    ),
    WorkflowName.PRODUCT_TO_OUTFIT: (
        WorkflowStep("FX-F05", "product_detail"),
        WorkflowStep("FX-F07", "create_outfit"),
    ),
    WorkflowName.SHOPPING_TO_COMMERCE: (
        WorkflowStep("FX-F10", "wishlist"),
        WorkflowStep("FX-F11", "checkout"),
    ),
    WorkflowName.ENGAGEMENT_TO_PERSONALIZATION: (
        WorkflowStep("FX-F13", "record_engagement"),
        WorkflowStep("FX-F09", "record_signal"),
    ),
}
