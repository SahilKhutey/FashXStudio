from api.app.tryon.domain.state_machine import can_transition


def test_all_nonterminal_states_have_a_defined_terminal_path() -> None:
    assert can_transition("queued", "cancelled")
    assert can_transition("inference", "failed")
    assert can_transition("quality_check", "completed")
