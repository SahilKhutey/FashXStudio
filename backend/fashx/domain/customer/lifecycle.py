from app.core.errors import ValidationError

from .enums import CustomerStatus

TRANSITIONS = {
    CustomerStatus.PENDING: {
        CustomerStatus.ACTIVE,
        CustomerStatus.CLOSED,
        CustomerStatus.DEACTIVATED,
    },
    CustomerStatus.ACTIVE: {
        CustomerStatus.SUSPENDED,
        CustomerStatus.CLOSED,
        CustomerStatus.DEACTIVATED,
    },
    CustomerStatus.SUSPENDED: {
        CustomerStatus.ACTIVE,
        CustomerStatus.CLOSED,
        CustomerStatus.DEACTIVATED,
    },
    CustomerStatus.CLOSED: set(),
    CustomerStatus.DEACTIVATED: set(),
}


def validate_transition(
    current: CustomerStatus,
    target: CustomerStatus,
) -> None:
    if target not in TRANSITIONS.get(
        current,
        set(),
    ):
        raise ValidationError(
            f"Invalid customer status transition from {current} to {target}"
        )


validate_customer_transition = validate_transition

