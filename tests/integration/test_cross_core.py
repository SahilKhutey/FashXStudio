from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.bootstrap import register_core_services
from app.core.context import CoreContext
from app.core.runtime import CoreRuntime
from app.domain.analytics.entities import AnalyticsEvent
from app.domain.analytics.enums import AnalyticsEventType
from app.domain.cart.entities import Cart, CartLine
from app.domain.cart.enums import CartOwnerType
from app.domain.checkout.entities import CheckoutSession
from app.domain.checkout.enums import CheckoutStatus
from app.domain.customer.entities import (
    Customer,
    CustomerAddress,
)
from app.domain.fulfillment.entities import (
    AddressSnapshot as FulfillmentAddressSnapshot,
)
from app.domain.fulfillment.entities import (
    Fulfillment,
    FulfillmentLine,
    Shipment,
)
from app.domain.fulfillment.enums import (
    FulfillmentStatus,
    ShipmentStatus,
)
from app.domain.order.entities import (
    Order,
    OrderAddressSnapshot,
    OrderLine,
)
from app.domain.order.events import OrderCreated
from app.domain.payments.entities import Payment
from app.domain.payments.events import PaymentCaptured
from app.domain.pricing.entities import Price
from app.integration.contracts import IntegrationMessage
from app.integration.dispatcher import IntegrationDispatcher
from app.integration.handlers import (
    OrderCompletedIntegrationHandler,
    PaymentCapturedIntegrationHandler,
)
from app.observability.correlation import (
    get_correlation_id,
    set_correlation_id,
)


@pytest.mark.asyncio
async def test_cross_core_e2e_flow():
    # 1. Initialize Runtime and Bootstrapped Services
    runtime = CoreRuntime()
    register_core_services(runtime)

    cid = uuid4()
    set_correlation_id(cid)
    assert get_correlation_id() == cid

    context = CoreContext.create(correlation_id=cid)

    # 2. Setup Integration Dispatcher & Handlers
    dispatcher = IntegrationDispatcher()
    order_handler = OrderCompletedIntegrationHandler()
    payment_handler = PaymentCapturedIntegrationHandler()

    dispatcher.register(OrderCreated, order_handler)
    dispatcher.register(PaymentCaptured, payment_handler)

    # 3. Customer Profile & Address Setup
    customer_service = runtime.registry.get("customer_service")
    customer_id = uuid4()
    customer = Customer(
        id=customer_id,
        email="sahil@example.com",
        first_name="Sahil",
        last_name="Khutey",
        phone="+919876543210",
    )
    address = CustomerAddress(
        customer_id=customer_id,
        recipient_name="Sahil Khutey",
        address_line_1="10 Fashion Boulevard",
        city="Raipur",
        state="Chhattisgarh",
        postal_code="492001",
    )
    await customer_service.create_customer(context=context, customer=customer)
    await customer_service.add_address(context=context, address=address)

    # 4. Pricing Setup
    pricing_service = runtime.registry.get("pricing_service")
    product_id = uuid4()
    price = Price(
        product_id=product_id,
        amount=Decimal("2500.00"),
        currency="INR",
    )
    await pricing_service.create_price(context=context, price=price)

    # 5. Cart Setup
    cart_service = runtime.registry.get("cart_service")
    cart_id = uuid4()
    cart = Cart(
        id=cart_id,
        customer_id=customer_id,
        owner_type=CartOwnerType.CUSTOMER,
    )
    await cart_service.create_cart(context=context, cart=cart)

    line_id = uuid4()
    cart_line = CartLine(
        id=line_id,
        cart_id=cart_id,
        product_id=product_id,
        quantity=2,
        unit_price=Decimal("2500.00"),
    )
    await cart_service.add_line(
        context=context,
        cart_id=cart_id,
        line=cart_line,
    )

    # 6. Checkout Flow
    checkout_service = runtime.registry.get("checkout_service")
    checkout_session = CheckoutSession(cart_id=cart_id)
    await checkout_service.create_checkout(
        context=context,
        checkout=checkout_session,
    )

    ready_session = await checkout_service.validate_checkout(
        context=context,
        checkout_id=checkout_session.id,
    )
    assert ready_session.status == CheckoutStatus.READY

    # 7. Convert Checkout to Immutable Order
    order_number = "ORD-2026-FASHX"
    order = Order(
        order_number=order_number,
        shipping_address=OrderAddressSnapshot(
            recipient_name=address.recipient_name,
            address_line_1=address.address_line_1,
            city=address.city,
            state=address.state,
            postal_code=address.postal_code,
        ),
    )
    order_lines = [
        OrderLine(
            product_id=product_id,
            title="Premium Designer Jacket",
            quantity=2,
            unit_price=Decimal("2500.00"),
        )
    ]

    created_order = await checkout_service.convert_to_order(
        context=context,
        checkout_id=checkout_session.id,
        order=order,
        lines=order_lines,
    )
    assert created_order.order_number == order_number
    assert created_order.grand_total == Decimal("5000.00")

    # Dispatch OrderCreated integration message
    order_event = OrderCreated(entity_id=created_order.id)
    await dispatcher.dispatch(
        IntegrationMessage(message_id=uuid4(), event=order_event)
    )
    assert len(order_handler.processed_orders) == 1

    # 8. Payment Flow
    payment_service = runtime.registry.get("payment_service")
    payment = Payment(
        order_id=created_order.id,
        amount=Decimal("5000.00"),
        currency="INR",
    )
    created_payment = await payment_service.create_payment(
        context=context,
        payment=payment,
    )
    await payment_service.authorize(
        context=context,
        payment_id=created_payment.id,
        payment_method="upi",
    )
    captured_payment = await payment_service.capture(
        context=context,
        payment_id=created_payment.id,
    )
    assert captured_payment.status.name == "CAPTURED"

    payment_event = PaymentCaptured(entity_id=captured_payment.id)
    await dispatcher.dispatch(
        IntegrationMessage(message_id=uuid4(), event=payment_event)
    )
    assert len(payment_handler.captured_payments) == 1

    # 9. Fulfillment Flow
    fulfillment_service = runtime.registry.get("fulfillment_service")
    fulfillment = Fulfillment(
        order_id=created_order.id,
        address=FulfillmentAddressSnapshot(
            recipient_name=address.recipient_name,
            address_line_1=address.address_line_1,
            city=address.city,
            state=address.state,
            postal_code=address.postal_code,
        ),
    )
    fulfillment_lines = [
        FulfillmentLine(
            order_line_id=order_lines[0].id,
            product_id=product_id,
            quantity=2,
        )
    ]
    created_fulfillment = await fulfillment_service.create_fulfillment(
        context=context,
        fulfillment=fulfillment,
        lines=fulfillment_lines,
    )
    await fulfillment_service.change_fulfillment_status(
        context=context,
        fulfillment_id=created_fulfillment.id,
        target=FulfillmentStatus.PROCESSING,
    )
    shipment = await fulfillment_service.create_shipment(
        context=context,
        fulfillment_id=created_fulfillment.id,
        shipment=Shipment(carrier="test-carrier"),
    )
    assert shipment.status == ShipmentStatus.LABEL_CREATED
    assert shipment.tracking_number is not None

    # 10. Analytics Ingestion
    analytics_service = runtime.registry.get("analytics_service")
    analytics_event = AnalyticsEvent(
        event_type=AnalyticsEventType.ORDER_COMPLETED,
        session_id=str(checkout_session.id),
        customer_id=customer_id,
        value=Decimal("5000.00"),
        properties={"order_id": str(created_order.id)},
    )
    recorded = await analytics_service.record_event(
        context=context,
        event=analytics_event,
    )
    assert recorded.event_type == AnalyticsEventType.ORDER_COMPLETED
    assert recorded.correlation_id == cid
