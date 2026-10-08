from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fashx.core.errors import ValidationError
from fashx.core.ids import new_id

from .enums import (
    AddressStatus,
    AddressType,
    ConsentType,
    CustomerStatus,
    CustomerType,
    PreferenceScope,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_customer_number() -> str:
    token = uuid4().hex[:10].upper()
    return f"FX-CUST-{token}"


@dataclass(slots=True)
class CustomerAddress:
    id: UUID = field(default_factory=new_id)
    customer_id: UUID | None = None
    address_type: AddressType = AddressType.HOME
    label: str = ""
    recipient_name: str = ""
    address_line_1: str = ""
    address_line_2: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = "IN"
    phone: str | None = None
    is_default: bool = False
    status: AddressStatus = AddressStatus.ACTIVE
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1

    def validate(self) -> None:
        if self.customer_id is None:
            raise ValidationError("Address requires customer ID.")

        required = {
            "recipient_name": self.recipient_name,
            "address_line_1": self.address_line_1,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }

        for field_name, value in required.items():
            if not value or not str(value).strip():
                raise ValidationError(f"{field_name} is required.")

        if self.version < 1:
            raise ValidationError("Address version must be positive.")

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.version += 1



@dataclass(slots=True)
class CustomerPreferences:
    customer_id: UUID | None = None
    preferred_currency: str = "INR"
    preferred_region: str | None = None
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    categories: list[str] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    sizes: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=utc_now)

    def validate(self) -> None:
        if len(self.preferred_currency) != 3:
            raise ValidationError("Currency must be a 3-character code.")

        if not self.language.strip():
            raise ValidationError("Language is required.")


@dataclass(slots=True)
class CustomerConsent:
    id: UUID = field(default_factory=new_id)
    customer_id: UUID | None = None
    consent_type: ConsentType = ConsentType.PRIVACY
    granted: bool = False
    version: str = "1.0"
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if self.customer_id is None:
            raise ValidationError("Consent requires customer_id.")

        if not self.version.strip():
            raise ValidationError("Consent version is required.")


@dataclass(slots=True)
class Customer:
    id: UUID = field(default_factory=new_id)
    customer_number: str = field(default_factory=generate_customer_number)
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    status: CustomerStatus = CustomerStatus.ACTIVE
    first_name: str = ""
    last_name: str = ""
    display_name: str = ""
    email: str | None = None
    phone: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    version: int = 1
    external_identity_id: str | None = None

    def validate(self) -> None:
        if not self.customer_number.strip():
            self.customer_number = generate_customer_number()

        if not (self.email or self.phone):
            raise ValidationError("Customer requires email or phone.")

        if self.email is not None and "@" not in self.email:
            raise ValidationError("Customer email is invalid.")

        if self.version < 1:
            raise ValidationError("Customer version must be positive.")

    def touch(self) -> None:
        self.version += 1
        self.updated_at = utc_now()



# Legacy support for single-key CustomerPreference
@dataclass(slots=True)
class CustomerPreference:
    id: UUID = field(default_factory=new_id)
    customer_id: UUID | None = None
    scope: PreferenceScope = PreferenceScope.COMMERCE
    key: str = ""
    value: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def validate(self) -> None:
        if self.customer_id is None:
            raise ValidationError("Preference requires customer ID.")
        if not self.key.strip():
            raise ValidationError("Preference key is required.")

    def touch(self) -> None:
        self.updated_at = utc_now()
