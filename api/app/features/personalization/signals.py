from .enums import SignalType

SIGNAL_WEIGHTS = {
    SignalType.VIEW: 0.1,
    SignalType.CLICK: 0.2,
    SignalType.LIKE: 0.4,
    SignalType.SAVE: 0.6,
    SignalType.SHARE: 0.5,
    SignalType.ADD_TO_CART: 0.7,
    SignalType.PURCHASE: 1.0,
    SignalType.SKIP: -0.1,
    SignalType.REJECT: -0.4,
    SignalType.REMOVE: -0.3,
}


def signal_strength(signal_type: SignalType) -> float:
    return SIGNAL_WEIGHTS[signal_type]
