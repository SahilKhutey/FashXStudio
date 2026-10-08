from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from fashx.core.bootstrap import register_core_services
from fashx.core.context import CoreContext
from fashx.core.errors import ConflictError, NotFoundError, ValidationError
from fashx.core.runtime import get_core_runtime
from fashx.domain.customer.entities import (
    Customer,
    CustomerAddress,
    CustomerConsent,
    CustomerPreference,
    CustomerPreferences,
    generate_customer_number,
)
from fashx.domain.customer.enums import (
    AddressType,
    ConsentType,
    PreferenceScope,
)
from fashx.domain.customer.service import CustomerService

from .customer_schemas import (
    AddressCreateRequest,
    AddressResponse,
    ConsentCreateRequest,
    ConsentResponse,
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
    PreferenceRequest,
    PreferenceResponse,
    PreferencesRequest,
    PreferencesResponse,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


def get_customer_service() -> CustomerService:
    register_core_services()
    return get_core_runtime().registry.get(
        "customer_service"
    )


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=201,
)
async def create_customer(
    payload: CustomerCreateRequest,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        customer = Customer(
            customer_number=generate_customer_number(),
            first_name=payload.first_name,
            last_name=payload.last_name,
            display_name=payload.display_name,
            email=payload.email,
            phone=payload.phone,
            external_identity_id=payload.external_identity_id,
        )

        result = await service.create_customer(
            context=CoreContext.create(),
            customer=customer,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return CustomerResponse(
        id=result.id,
        customer_number=result.customer_number,
        status=result.status.value,
        customer_type=result.customer_type.value,
        first_name=result.first_name,
        last_name=result.last_name,
        display_name=result.display_name,
        email=result.email,
        phone=result.phone,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def get_customer(
    customer_id: UUID,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        result = await service.get_customer(customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return CustomerResponse(
        id=result.id,
        customer_number=result.customer_number,
        status=result.status.value,
        customer_type=result.customer_type.value,
        first_name=result.first_name,
        last_name=result.last_name,
        display_name=result.display_name,
        email=result.email,
        phone=result.phone,
    )


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdateRequest,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        customer = await service.get_customer(customer_id)
        if payload.first_name is not None:
            customer.first_name = payload.first_name
        if payload.last_name is not None:
            customer.last_name = payload.last_name
        if payload.phone is not None:
            customer.phone = payload.phone

        result = await service.update_customer(
            context=CoreContext.create(),
            customer=customer,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return CustomerResponse(
        id=result.id,
        customer_number=result.customer_number,
        status=result.status.value,
        customer_type=result.customer_type.value,
        first_name=result.first_name,
        last_name=result.last_name,
        display_name=result.display_name,
        email=result.email,
        phone=result.phone,
    )


@router.post(
    "/{customer_id}/addresses",
    response_model=AddressResponse,
    status_code=201,
)
async def add_address(
    customer_id: UUID,
    payload: AddressCreateRequest,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        address = CustomerAddress(
            customer_id=customer_id,
            address_type=AddressType(payload.address_type),
            label=payload.label,
            recipient_name=payload.recipient_name,
            address_line_1=payload.address_line_1,
            address_line_2=payload.address_line_2,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            country=payload.country,
            phone=payload.phone,
            is_default=payload.is_default,
        )

        result = await service.add_address(
            context=CoreContext.create(),
            address=address,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return AddressResponse(
        id=result.id,
        customer_id=result.customer_id,
        address_type=result.address_type.value,
        label=result.label,
        recipient_name=result.recipient_name,
        address_line_1=result.address_line_1,
        address_line_2=result.address_line_2,
        city=result.city,
        state=result.state,
        postal_code=result.postal_code,
        country=result.country,
        phone=result.phone,
        is_default=result.is_default,
        status=result.status.value,
    )


@router.get(
    "/{customer_id}/addresses",
    response_model=list[AddressResponse],
)
async def list_addresses(
    customer_id: UUID,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        await service.get_customer(customer_id)
        addresses = await service.address_repository.list_by_customer(customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [
        AddressResponse(
            id=addr.id,
            customer_id=addr.customer_id,
            address_type=addr.address_type.value,
            label=addr.label,
            recipient_name=addr.recipient_name,
            address_line_1=addr.address_line_1,
            address_line_2=addr.address_line_2,
            city=addr.city,
            state=addr.state,
            postal_code=addr.postal_code,
            country=addr.country,
            phone=addr.phone,
            is_default=addr.is_default,
            status=addr.status.value,
        )
        for addr in addresses
    ]


@router.put(
    "/{customer_id}/preferences",
    response_model=PreferencesResponse,
)
async def save_preferences(
    customer_id: UUID,
    payload: PreferencesRequest,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        prefs = CustomerPreferences(
            customer_id=customer_id,
            preferred_currency=payload.preferred_currency,
            preferred_region=payload.preferred_region,
            language=payload.language,
            timezone=payload.timezone,
            categories=payload.categories,
            brands=payload.brands,
            styles=payload.styles,
            sizes=payload.sizes,
        )

        result = await service.save_preferences(
            context=CoreContext.create(),
            preferences=prefs,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PreferencesResponse(
        customer_id=result.customer_id,
        preferred_currency=result.preferred_currency,
        preferred_region=result.preferred_region,
        language=result.language,
        timezone=result.timezone,
        categories=result.categories,
        brands=result.brands,
        styles=result.styles,
        sizes=result.sizes,
    )


# Legacy support for POST preferences
@router.post(
    "/{customer_id}/preferences",
    response_model=PreferenceResponse,
    status_code=201,
)
async def legacy_save_preference(
    customer_id: UUID,
    payload: PreferenceRequest,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        pref = CustomerPreference(
            customer_id=customer_id,
            scope=PreferenceScope(payload.scope),
            key=payload.key,
            value=payload.value,
        )
        result = await service.set_preference(
            context=CoreContext.create(),
            preference=pref,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PreferenceResponse(
        id=result.id,
        customer_id=result.customer_id,
        scope=result.scope.value,
        key=result.key,
        value=result.value,
    )



@router.post(
    "/{customer_id}/consents",
    response_model=ConsentResponse,
    status_code=201,
)
async def save_consent(
    customer_id: UUID,
    payload: ConsentCreateRequest,
    service: CustomerService = Depends(
        get_customer_service
    ),
):
    try:
        consent = CustomerConsent(
            customer_id=customer_id,
            consent_type=ConsentType(payload.consent_type),
            granted=payload.granted,
            version=payload.version,
        )

        result = await service.save_consent(
            context=CoreContext.create(),
            consent=consent,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ConsentResponse(
        id=result.id,
        customer_id=result.customer_id,
        consent_type=result.consent_type.value,
        granted=result.granted,
        version=result.version,
    )
