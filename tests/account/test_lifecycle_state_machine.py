from datetime import UTC, datetime
from uuid import uuid4

from database.models.identity import User
from fashx.account.schemas import AccountStatus


def test_account_status_enum_values():
    assert AccountStatus.PENDING_VERIFICATION.value == "PENDING_VERIFICATION"
    assert AccountStatus.PROVISIONING.value == "PROVISIONING"
    assert AccountStatus.ACTIVE.value == "ACTIVE"
    assert AccountStatus.DISABLED.value == "DISABLED"
    assert AccountStatus.DELETION_PENDING.value == "DELETION_PENDING"
    assert AccountStatus.DELETION_IN_PROGRESS.value == "DELETION_IN_PROGRESS"
    assert AccountStatus.DELETED.value == "DELETED"


def test_user_model_defaults():
    uid = uuid4()
    user = User(id=uid, status=AccountStatus.ACTIVE.value, email_verified=False)
    assert user.status == "ACTIVE"
    assert user.email_verified is False
    assert user.email_normalized is None
    assert user.activated_at is None
    assert user.disabled_at is None
    assert user.deletion_requested_at is None
    assert user.deleted_at is None


def test_user_state_transitions():
    user = User(
        id=uuid4(),
        status=AccountStatus.PENDING_VERIFICATION.value,
        email_normalized="test@example.com",
    )
    assert user.status == "PENDING_VERIFICATION"

    # Transition to ACTIVE on email verification
    user.email_verified = True
    user.status = AccountStatus.ACTIVE.value
    user.activated_at = datetime.now(UTC)
    assert user.status == "ACTIVE"
    assert user.activated_at is not None

    # Transition to DISABLED
    user.status = AccountStatus.DISABLED.value
    user.disabled_at = datetime.now(UTC)
    assert user.status == "DISABLED"
    assert user.disabled_at is not None

    # Transition to DELETION_PENDING
    user.status = AccountStatus.DELETION_PENDING.value
    user.deletion_requested_at = datetime.now(UTC)
    assert user.status == "DELETION_PENDING"
    assert user.deletion_requested_at is not None

    # Transition to DELETION_IN_PROGRESS
    user.status = AccountStatus.DELETION_IN_PROGRESS.value
    assert user.status == "DELETION_IN_PROGRESS"

    # Transition to DELETED (terminal)
    user.status = AccountStatus.DELETED.value
    user.deleted_at = datetime.now(UTC)
    assert user.status == "DELETED"
    assert user.deleted_at is not None
