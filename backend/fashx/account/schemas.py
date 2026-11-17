from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AccountStatus(str, Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    DELETION_PENDING = "DELETION_PENDING"
    DELETION_IN_PROGRESS = "DELETION_IN_PROGRESS"
    DELETED = "DELETED"


class AccountProvisionRequest(BaseModel):
    email: EmailStr | None = None
    email_verified: bool = False
    device_label: str | None = Field(default=None, max_length=128)


class AccountProvisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    status: AccountStatus
    email_normalized: str | None = None
    email_verified: bool
    is_new: bool


class AccountMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email_normalized: str | None = None
    email_verified: bool
    status: AccountStatus
    roles: list[str]
    created_at: datetime


class EmailChangeRequest(BaseModel):
    new_email: EmailStr


class EmailChangeResponse(BaseModel):
    message: str
    status: str = "verification_sent"


class EmailChangeConfirmRequest(BaseModel):
    new_email: EmailStr
    confirmation_code: str = Field(min_length=6, max_length=32)


class EmailChangeConfirmResponse(BaseModel):
    user_id: str
    email_normalized: str
    status: str = "confirmed"


class AccountDisableRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class AccountDisableResponse(BaseModel):
    user_id: str
    status: AccountStatus
    disabled_at: datetime


class AccountDeletionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class AccountDeletionResponse(BaseModel):
    job_id: str
    user_id: str
    status: AccountStatus
    message: str


class AccountDeletionStatusResponse(BaseModel):
    job_id: str
    user_id: str
    status: str
    requested_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    attempts: int


class SessionRevokeAllResponse(BaseModel):
    user_id: str
    revoked_sessions_count: int
    message: str
