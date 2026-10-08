"""Unit Tests for FashXStudio Production Visual Integration, Verification & Release Framework (Phase 16 - FINAL).

Tests the 9-layer production model, screen and navigation registries, token governance,
release gate audits, visual quality checklists, golden artifacts, E2E journeys,
and strict Constitution Rule I02 (Contract Primacy) enforcement with extra="forbid".
"""

import pytest
from pydantic import ValidationError

from schemas.visual.release import (
    EndToEndJourneySpecContract,
    GoldenArtifactContract,
    GoldenArtifactType,
    NavigationRegistryEntryContract,
    ProductionLayer,
    ProductionReleaseReportContract,
    QualityCategory,
    ReleaseEnvironment,
    ReleaseGateResultContract,
    ReleaseGateStatus,
    ScreenRegistryEntryContract,
    TokenValidationReportContract,
    TokenValidationRequestContract,
    VisualChecklistItemContract,
    VisualReleaseGateAuditRequest,
    VisualTrackStatusContract,
)
from fashx.visual.release_service import (
    get_e2e_journeys,
    get_golden_artifacts,
    get_navigation_registry,
    get_screen_registry,
    get_visual_quality_checklist,
    get_visual_track_completion_status,
    run_production_release_gate,
    validate_token_reference,
)


# ---------------------------------------------------------------------------
# Domain Unit Tests
# ---------------------------------------------------------------------------

def test_rel_unit_001_layer_model_enum() -> None:
    """REL-UNIT-001: Validate all 9 production layers (Section 16.4)."""
    expected_layers = {
        "layer_0_platform",
        "layer_1_shell",
        "layer_2_design_system",
        "layer_3_features",
        "layer_4_templates",
        "layer_5_screens",
        "layer_6_services",
        "layer_7_analytics",
        "layer_8_qa",
    }
    actual_layers = {layer.value for layer in ProductionLayer}
    assert actual_layers == expected_layers
    assert len(actual_layers) == 9


def test_rel_unit_002_screen_registry_integrity() -> None:
    """REL-UNIT-002: Validate screen registry entries and metadata (Section 16.14)."""
    screens = get_screen_registry()
    assert len(screens) >= 15

    screen_ids = [s.screen_id for s in screens]
    assert "D01" in screen_ids
    assert "P01" in screen_ids
    assert "P03" in screen_ids
    assert "DT01" in screen_ids
    assert "ST02" in screen_ids
    assert "M02" in screen_ids
    assert "AI01" in screen_ids
    assert "AI03" in screen_ids
    assert "PR01" in screen_ids
    assert "PR08" in screen_ids

    for screen in screens:
        assert screen.route.startswith("/")
        assert screen.title != ""
        assert screen.template != ""
        assert screen.feature != ""
        assert screen.accessibility_role in {"main", "region", "search"}
        assert screen.is_production_ready is True


def test_rel_unit_003_navigation_registry_integrity() -> None:
    """REL-UNIT-003: Validate navigation registry routing and groups (Section 16.13)."""
    nav_items = get_navigation_registry()
    assert len(nav_items) >= 7

    routes = [item.route for item in nav_items]
    assert "/discovery" in routes
    assert "/shop/catalog" in routes
    assert "/styling/builder" in routes
    assert "/geography/map" in routes
    assert "/ai/home" in routes
    assert "/profile/dashboard" in routes

    groups = {item.group for item in nav_items}
    assert "primary" in groups
    assert "profile" in groups
    assert "secondary" in groups


def test_rel_unit_004_token_validation_valid_reference() -> None:
    """REL-UNIT-004: Validate token reference resolution to primitive (Section 16.10 & 16.11)."""
    req = TokenValidationRequestContract(
        token_name="color.text.primary",
        token_category="color",
        primitive_ref="gray-900",
        semantic_usage="Primary body text across all screens",
        theme="light",
    )
    report = validate_token_reference(req)
    assert report.is_valid is True
    assert report.resolved_value == "#111827"
    assert report.hierarchy_valid is True
    assert len(report.errors) == 0


def test_rel_unit_005_token_validation_rogue_and_unresolvable() -> None:
    """REL-UNIT-005: Reject rogue tokens and unresolvable primitives (Section 16.6)."""
    req_rogue = TokenValidationRequestContract(
        token_name="rogue.custom.neonPink",
        token_category="color",
        primitive_ref="unknown-pink",
        semantic_usage="Ad-hoc button accent",
    )
    report_rogue = validate_token_reference(req_rogue)
    assert report_rogue.is_valid is False
    assert report_rogue.hierarchy_valid is False
    assert any("forbidden by Section 16.6" in err for err in report_rogue.errors)
    assert any("Unresolvable primitive reference" in err for err in report_rogue.errors)


def test_rel_unit_006_token_validation_circular_reference() -> None:
    """REL-UNIT-006: Reject circular token self-references (Section 16.11)."""
    req_circular = TokenValidationRequestContract(
        token_name="spacing.md",
        token_category="spacing",
        primitive_ref="spacing.md",
        semantic_usage="Default card padding",
    )
    report_circular = validate_token_reference(req_circular)
    assert report_circular.is_valid is False
    assert any("Circular token reference detected" in err for err in report_circular.errors)


def test_rel_unit_007_production_release_gate_audit() -> None:
    """REL-UNIT-007: Execute comprehensive 5-gate production release audit (Section 16.56)."""
    audit_req = VisualReleaseGateAuditRequest(
        release_version="v1.0.0-rc1",
        environment=ReleaseEnvironment.STAGING,
        include_e2e=True,
        include_a11y=True,
    )
    report = run_production_release_gate(audit_req)
    assert report.overall_passed is True
    assert len(report.gates) == 5

    gate_names = [g.gate_name for g in report.gates]
    assert "functional" in gate_names
    assert "visual" in gate_names
    assert "accessibility" in gate_names
    assert "performance" in gate_names
    assert "integration" in gate_names

    for gate in report.gates:
        assert gate.passed is True
        assert gate.score >= 95.0
        assert gate.status == ReleaseGateStatus.PASSED


def test_rel_unit_008_visual_quality_checklist_categories() -> None:
    """REL-UNIT-008: Verify checklist spans all 13 categories (Section 16.57)."""
    checklist = get_visual_quality_checklist()
    assert len(checklist) >= 20

    categories = {item.category for item in checklist}
    assert QualityCategory.FOUNDATION in categories
    assert QualityCategory.SHELL in categories
    assert QualityCategory.COMPONENTS in categories
    assert QualityCategory.FASHION in categories
    assert QualityCategory.SHOPPING in categories
    assert QualityCategory.DISCOVERY in categories
    assert QualityCategory.STYLING in categories
    assert QualityCategory.GEOGRAPHY in categories
    assert QualityCategory.AI in categories
    assert QualityCategory.PERSONAL in categories
    assert QualityCategory.RESPONSIVE in categories
    assert QualityCategory.ACCESSIBILITY in categories
    assert QualityCategory.QA in categories

    for item in checklist:
        assert item.item_id.startswith("CHK-")
        assert item.is_verified is True


def test_rel_unit_009_e2e_journeys_spec() -> None:
    """REL-UNIT-009: Verify E2E-001 through E2E-005 journeys (Section 16.36)."""
    journeys = get_e2e_journeys()
    assert len(journeys) == 5

    journey_ids = [j.journey_id for j in journeys]
    assert journey_ids == ["E2E-001", "E2E-002", "E2E-003", "E2E-004", "E2E-005"]

    for j in journeys:
        assert len(j.steps) >= 5
        assert j.status == ReleaseGateStatus.PASSED


def test_rel_unit_010_golden_artifacts_count_and_thresholds() -> None:
    """REL-UNIT-010: Verify 15 Golden Screens and 15 Golden Components (Section 16.38 & 16.39)."""
    artifacts = get_golden_artifacts()
    assert len(artifacts) == 30

    screens = [a for a in artifacts if a.artifact_type == GoldenArtifactType.SCREEN]
    components = [a for a in artifacts if a.artifact_type == GoldenArtifactType.COMPONENT]

    assert len(screens) == 15
    assert len(components) == 15

    for a in artifacts:
        assert a.match_threshold <= 0.05
        assert a.status == ReleaseGateStatus.PASSED


def test_rel_unit_011_master_track_completion_status() -> None:
    """REL-UNIT-011: Verify 100% completion of VD-00 through VD-16 (Section 16.61 & 16.62)."""
    status = get_visual_track_completion_status()
    assert status.total_phases == 17
    assert len(status.phase_statuses) == 17

    for phase_id in [f"VD-{i:02d}" for i in range(17)]:
        assert status.phase_statuses[phase_id] == "100%"

    assert status.visual_design_architecture_pct == 100
    assert status.visual_specification_pct == 100
    # Rule from 16.61: ACTUAL REPOSITORY IMPLEMENTATION 0% (Handoff state)
    assert status.actual_repository_implementation_pct == 0
    assert "COMPLETE & VERIFIED" in status.status_message


# ---------------------------------------------------------------------------
# Strict Contract Rejection Tests (Rule I02: extra="forbid")
# ---------------------------------------------------------------------------

def test_forbid_001_screen_registry_entry_contract() -> None:
    """FORBID-001: ScreenRegistryEntryContract rejects rogue fields."""
    with pytest.raises(ValidationError):
        ScreenRegistryEntryContract(
            screen_id="D99",
            route="/rogue",
            title="Rogue Screen",
            template="T01",
            feature="rogue",
            accessibility_role="main",
            analytics_tag="rogue_tag",
            rogue_field="unauthorized",
        )


def test_forbid_002_navigation_registry_entry_contract() -> None:
    """FORBID-002: NavigationRegistryEntryContract rejects rogue fields."""
    with pytest.raises(ValidationError):
        NavigationRegistryEntryContract(
            route="/test",
            label="Test",
            icon="icon",
            group="primary",
            screen_id="D01",
            extra_field="rejected",
        )


def test_forbid_003_token_validation_request_contract() -> None:
    """FORBID-003: TokenValidationRequestContract rejects rogue fields."""
    with pytest.raises(ValidationError):
        TokenValidationRequestContract(
            token_name="color.test",
            token_category="color",
            primitive_ref="gray-900",
            semantic_usage="Test",
            unauthorized_prop=123,
        )


def test_forbid_004_token_validation_report_contract() -> None:
    """FORBID-004: TokenValidationReportContract rejects rogue fields."""
    with pytest.raises(ValidationError):
        TokenValidationReportContract(
            token_name="color.test",
            is_valid=True,
            hierarchy_valid=True,
            bogus_key=True,
        )


def test_forbid_005_release_gate_result_contract() -> None:
    """FORBID-005: ReleaseGateResultContract rejects rogue fields."""
    with pytest.raises(ValidationError):
        ReleaseGateResultContract(
            gate_name="visual",
            status=ReleaseGateStatus.PASSED,
            score=100.0,
            passed=True,
            timestamp="2026-10-02T12:00:00Z",
            extra_metric="failed",
        )


def test_forbid_006_visual_release_gate_audit_request() -> None:
    """FORBID-006: VisualReleaseGateAuditRequest rejects rogue fields."""
    with pytest.raises(ValidationError):
        VisualReleaseGateAuditRequest(
            release_version="v1.0.0",
            rogue_param=True,
        )


def test_forbid_007_visual_checklist_item_contract() -> None:
    """FORBID-007: VisualChecklistItemContract rejects rogue fields."""
    with pytest.raises(ValidationError):
        VisualChecklistItemContract(
            item_id="CHK-01",
            category=QualityCategory.FOUNDATION,
            title="Title",
            description="Desc",
            rogue_attr="forbidden",
        )


def test_forbid_008_end_to_end_journey_spec_contract() -> None:
    """FORBID-008: EndToEndJourneySpecContract rejects rogue fields."""
    with pytest.raises(ValidationError):
        EndToEndJourneySpecContract(
            journey_id="E2E-001",
            name="Journey",
            steps=["Step 1"],
            status=ReleaseGateStatus.PASSED,
            verified_at="2026-10-02T12:00:00Z",
            extra_attribute="illegal",
        )
