from __future__ import annotations

from enum import StrEnum


class PaymentStatus(StrEnum):
    CREATED = "created"
    REQUIRES_ACTION = "requires_action"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethodType(StrEnum):
    CARD = "card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"
    COD = "cod"
    OTHER = "other"


class TransactionType(StrEnum):
    AUTHORIZATION = "authorization"
    CAPTURE = "capture"
    VOID = "void"
    REFUND = "refund"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
