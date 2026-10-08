from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from fashx.core.bootstrap import register_core_services
from fashx.core.context import CoreContext
from fashx.core.runtime import get_core_runtime
from fashx.domain.cart.entities import (
    Cart,
    CartLine,
)
from fashx.domain.cart.service import (
    CartService,
)

from .cart_schemas import (
    CartCreateRequest,
    CartLineCreateRequest,
    CartLineResponse,
    CartResponse,
    CartTotalsResponse,
    QuantityUpdateRequest,
)

router = APIRouter(
    prefix="/cart",
    tags=["cart"],
)


def get_cart_service() -> CartService:
    register_core_services()
    return get_core_runtime().registry.get(
        "cart_service"
    )


def cart_response(
    cart: Cart,
) -> CartResponse:
    return CartResponse(
        id=cart.id,
        owner_type=cart.owner_type,
        customer_id=cart.customer_id,
        session_id=cart.session_id,
        status=cart.status,
        currency=cart.currency,
        version=cart.version,
    )


def line_response(
    line: CartLine,
) -> CartLineResponse:
    return CartLineResponse(
        id=line.id,
        cart_id=line.cart_id,
        product_id=line.product_id,
        variant_id=line.variant_id,
        listing_id=line.listing_id,
        quantity=line.quantity,
        unit_price=line.unit_price,
        currency=line.currency,
    )


@router.post(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cart(
    payload: CartCreateRequest,
    service: CartService = Depends(
        get_cart_service
    ),
):
    cart = Cart(
        owner_type=payload.owner_type,
        customer_id=payload.customer_id,
        session_id=payload.session_id,
        currency=payload.currency.upper(),
    )

    result = await service.create_cart(
        context=CoreContext.create(),
        cart=cart,
    )

    return cart_response(result)


@router.get(
    "/{cart_id}",
    response_model=CartResponse,
)
async def get_cart(
    cart_id: UUID,
    service: CartService = Depends(
        get_cart_service
    ),
):
    result = await service.get_cart(
        cart_id
    )

    return cart_response(result)


@router.post(
    "/{cart_id}/lines",
    response_model=CartLineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_line(
    cart_id: UUID,
    payload: CartLineCreateRequest,
    service: CartService = Depends(
        get_cart_service
    ),
):
    line = CartLine(
        cart_id=cart_id,
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        listing_id=payload.listing_id,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        currency=payload.currency.upper(),
    )

    result = await service.add_line(
        context=CoreContext.create(),
        cart_id=cart_id,
        line=line,
    )

    return line_response(result)


@router.patch(
    "/lines/{line_id}",
    response_model=CartLineResponse,
)
async def update_quantity(
    line_id: UUID,
    payload: QuantityUpdateRequest,
    service: CartService = Depends(
        get_cart_service
    ),
):
    result = await service.update_quantity(
        context=CoreContext.create(),
        line_id=line_id,
        quantity=payload.quantity,
    )

    return line_response(result)


@router.delete(
    "/lines/{line_id}",
    response_model=CartLineResponse,
)
async def remove_line(
    line_id: UUID,
    service: CartService = Depends(
        get_cart_service
    ),
):
    result = await service.remove_line(
        context=CoreContext.create(),
        line_id=line_id,
    )

    return line_response(result)


@router.delete(
    "/{cart_id}/lines",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_cart(
    cart_id: UUID,
    service: CartService = Depends(
        get_cart_service
    ),
):
    await service.clear_cart(
        context=CoreContext.create(),
        cart_id=cart_id,
    )

    return None


@router.get(
    "/{cart_id}/totals",
    response_model=CartTotalsResponse,
)
async def cart_totals(
    cart_id: UUID,
    service: CartService = Depends(
        get_cart_service
    ),
):
    result = await service.calculate_totals(
        cart_id
    )

    return CartTotalsResponse(
        subtotal=result.subtotal,
        item_count=result.item_count,
        currency=result.currency,
    )
