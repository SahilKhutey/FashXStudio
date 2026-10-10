"""Tests for stage-level timing instrumentation and Server-Timing headers."""

import time

from fashx.observability.stages import (
    format_server_timing,
    get_current_stages,
    stage,
    start_stage_recording,
)


def test_stage_context_manager_records_durations() -> None:
    start_stage_recording()

    with stage("retrieval"):
        time.sleep(0.01)

    with stage("scoring"):
        time.sleep(0.005)

    stages = get_current_stages()
    assert "retrieval" in stages
    assert "scoring" in stages
    assert stages["retrieval"] >= 8.0
    assert stages["scoring"] >= 4.0

    header = format_server_timing()
    assert "retrieval;dur=" in header
    assert "scoring;dur=" in header
