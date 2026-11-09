from scripts.rc10.beta_gates import (
    REQUIRED_GATES,
    evaluate_beta_gates,
)


def test_all_gates_pass():
    gates = dict.fromkeys(REQUIRED_GATES, True)
    result = evaluate_beta_gates(gates)
    assert result.decision == "GO"
    assert not result.blocked
    assert not result.missing


def test_missing_gate_holds_release():
    gates = dict.fromkeys(REQUIRED_GATES[:-1], True)
    result = evaluate_beta_gates(gates)
    assert result.decision == "HOLD"
    assert REQUIRED_GATES[-1] in result.missing


def test_failed_gate_holds_release():
    gates = dict.fromkeys(REQUIRED_GATES, True)
    gates["B5_privacy"] = False
    result = evaluate_beta_gates(gates)
    assert result.decision == "HOLD"
    assert "B5_privacy" in result.blocked


def test_empty_gates_hold_release():
    result = evaluate_beta_gates({})
    assert result.decision == "HOLD"
    assert len(result.missing) == len(REQUIRED_GATES)
