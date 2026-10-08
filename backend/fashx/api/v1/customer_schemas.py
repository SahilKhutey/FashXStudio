from uuid import UUID

from pydantic import BaseModel, Field


class CustomerCreateRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    display_name: str = ""
    email: str | None = None
    phone: str | None = None
    external_identity_id: str | None = None



class CustomerResponse(BaseModel):
    id: UUID
    customer_number: str
    status: str
    customer_type: str
    first_name: str
    last_name: str
    display_name: str
    email: str | None = None
    phone: str | None = None


class AddressCreateRequest(BaseModel):
    address_type: str = "shipping"
    label: str = ""
    recipient_name: str
    address_line_1: str
    address_line_2: str = ""
    city: str
    state: str
    postal_code: str
    country: str = "IN"
    phone: str | None = None
    is_default: bool = False


class AddressResponse(BaseModel):
    id: UUID
    customer_id: UUID | None = None
    address_type: str
    label: str = ""
    recipient_name: str
    address_line_1: str
    address_line_2: str = ""
    city: str
    state: str
    postal_code: str
    country: str
    phone: str | None = None
    is_default: bool = False
    status: str = "active"


class PreferencesRequest(BaseModel):
    preferred_currency: str = "INR"
    preferred_region: str | None = None
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    categories: list[str] = Field(default_factory=list)
    brands: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    sizes: dict[str, str] = Field(default_factory=dict)


class PreferencesResponse(BaseModel):
    customer_id: UUID | None = None
    preferred_currency: str = "INR"
    preferred_region: str | None = None
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    categories: list[str] = Field(default_factory=list)
    brands: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    sizes: dict[str, str] = Field(default_factory=dict)


class ConsentCreateRequest(BaseModel):
    consent_type: str = "privacy"
    granted: bool = False
    version: str = "1.0"


class ConsentResponse(BaseModel):
    id: UUID
    customer_id: UUID | None = None
    consent_type: str
    granted: bool
    version: str


# Legacy schemas support
class CustomerUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class PreferenceRequest(BaseModel):
    scope: str = "commerce"
    key: str
    value: str


class PreferenceResponse(BaseModel):
    id: UUID | None = None
    customer_id: UUID
    scope: str
    key: str
    value: str
