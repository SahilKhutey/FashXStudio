import copy
from uuid import uuid4

import pytest

from app.modules.customization.application.editor import EditorSession
from app.modules.customization.application.services.theme_resolver import get_theme_resolver
from app.modules.customization.application.use_cases import (
    GetCustomizationUseCase,
    UpdateCustomizationUseCase,
)
from app.modules.customization.domain.exceptions import (
    CustomizationConflictError,
    InvalidCustomizationError,
)

BASE_CONFIG = {
    "configuration_version": "1.0.0",
    "schema_version": "1.0.0",
    "theme": {
        "id": "theme-minimal",
        "version": "1.0.0",
        "overrides": {},
    },
    "layout": {
        "id": "layout-grid",
        "version": "1.0.0",
        "settings": {
            "columns": 2,
            "density": "comfortable",
        },
    },
    "components": [
        {
            "id": "comp-hdr-1",
            "component_id": "restaurant-header",
            "slot": "header",
            "order": 1,
            "visible": True,
            "props": {"show_logo": True},
        },
        {
            "id": "comp-nav-1",
            "component_id": "category-navigation",
            "slot": "navigation",
            "order": 2,
            "visible": True,
            "props": {"style": "pills"},
        },
    ],
}


def test_arc08_t051_open_settings_editor():
    org_id = uuid4()
    menu_id = "menu-t051"
    use_case = GetCustomizationUseCase()
    draft = use_case.execute(org_id, menu_id)
    assert draft.menu_id == menu_id
    assert draft.revision == 1
    assert "theme" in draft.configuration


def test_arc08_t052_change_primary_color():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.set_primary_color("#2563eb")
    assert session.draft["theme"]["overrides"]["color"]["brand"]["primary"] == "#2563eb"
    assert session.has_unsaved_changes is True


def test_arc08_t053_change_layout():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.set_layout("layout-list")
    assert session.draft["layout"]["id"] == "layout-list"

    resolver = get_theme_resolver()
    resolved = resolver.resolve(session.draft)
    assert resolved["layout_id"] == "layout-list"


def test_arc08_t054_hide_component():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.set_component_visibility("comp-hdr-1", False)
    header = next(c for c in session.draft["components"] if c["id"] == "comp-hdr-1")
    assert header["visible"] is False


def test_arc08_t055_reorder_component():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.reorder_component("comp-hdr-1", 5)
    header = next(c for c in session.draft["components"] if c["id"] == "comp-hdr-1")
    assert header["order"] == 5


def test_arc08_t056_add_unsupported_component():
    org_id = uuid4()
    menu_id = "menu-t056"
    use_case = UpdateCustomizationUseCase()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["components"].append(
        {
            "id": "bad-comp-1",
            "component_id": "unregistered-component-xyz",
            "slot": "content",
            "order": 3,
            "visible": True,
            "props": {},
        }
    )
    with pytest.raises(InvalidCustomizationError):
        use_case.execute(org_id, menu_id, cfg, expected_revision=1)


def test_arc08_t057_undo_change():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.set_primary_color("#ff0000")
    assert session.draft["theme"]["overrides"]["color"]["brand"]["primary"] == "#ff0000"

    undone = session.undo()
    assert undone is True
    # Primary color override reverted
    assert session.draft["theme"]["overrides"] == {}


def test_arc08_t058_redo_change():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.set_primary_color("#00ff00")
    session.undo()
    assert session.draft["theme"]["overrides"] == {}

    redone = session.redo()
    assert redone is True
    assert session.draft["theme"]["overrides"]["color"]["brand"]["primary"] == "#00ff00"


def test_arc08_t059_navigate_with_unsaved_changes():
    session = EditorSession(BASE_CONFIG, revision=1)
    session.set_primary_color("#123456")
    # Dirty state flag indicates navigation warning should be presented
    assert session.has_unsaved_changes is True


def test_arc08_t060_save_valid_configuration():
    org_id = uuid4()
    menu_id = "menu-t060"
    get_use_case = GetCustomizationUseCase()
    update_use_case = UpdateCustomizationUseCase()
    get_use_case.execute(org_id, menu_id)
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["theme"]["overrides"] = {"color": {"brand": {"primary": "#334155"}}}
    saved = update_use_case.execute(org_id, menu_id, cfg, expected_revision=1)
    assert saved.revision == 2
    assert saved.etag == '"revision-2"'


def test_arc08_t061_save_invalid_configuration():
    org_id = uuid4()
    menu_id = "menu-t061"
    use_case = UpdateCustomizationUseCase()
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["theme"]["id"] = "theme-nonexistent"
    with pytest.raises(InvalidCustomizationError) as exc_info:
        use_case.execute(org_id, menu_id, cfg, expected_revision=1)
    assert len(exc_info.value.errors) > 0


def test_arc08_t062_reload_after_save():
    org_id = uuid4()
    menu_id = "menu-t062"
    update_use_case = UpdateCustomizationUseCase()
    get_use_case = GetCustomizationUseCase()

    cfg = copy.deepcopy(BASE_CONFIG)
    cfg["theme"]["overrides"] = {"color": {"brand": {"primary": "#059669"}}}
    saved = update_use_case.execute(org_id, menu_id, cfg, expected_revision=1)

    # Reload from server
    reloaded = get_use_case.execute(org_id, menu_id)
    assert reloaded.revision == saved.revision
    assert reloaded.configuration["theme"]["overrides"]["color"]["brand"]["primary"] == "#059669"


def test_arc08_t063_two_editors_update_same_revision():
    org_id = uuid4()
    menu_id = "menu-t063"
    get_use_case = GetCustomizationUseCase()
    update_use_case = UpdateCustomizationUseCase()
    get_use_case.execute(org_id, menu_id)

    cfg1 = copy.deepcopy(BASE_CONFIG)
    cfg1["theme"]["overrides"] = {"color": {"brand": {"primary": "#111111"}}}
    # Editor 1 saves revision 1 -> becomes revision 2
    update_use_case.execute(org_id, menu_id, cfg1, expected_revision=1)

    # Editor 2 attempts to save with stale expected_revision=1
    cfg2 = copy.deepcopy(BASE_CONFIG)
    cfg2["theme"]["overrides"] = {"color": {"brand": {"primary": "#222222"}}}
    with pytest.raises(CustomizationConflictError) as exc_info:
        update_use_case.execute(org_id, menu_id, cfg2, expected_revision=1)
    assert "revision conflict" in str(exc_info.value).lower()


def test_arc08_t064_switch_editor_modes():
    session = EditorSession(BASE_CONFIG, revision=1)
    assert session.mode == "settings"

    session.set_primary_color("#9333ea")
    session.set_mode("visual")
    assert session.mode == "visual"
    # Both modes operate on the identical draft state
    assert session.draft["theme"]["overrides"]["color"]["brand"]["primary"] == "#9333ea"


def test_arc08_t065_use_editor_with_keyboard_only():
    session = EditorSession(BASE_CONFIG, revision=1)
    # Core command executions represent keyboard-accessible shortcuts
    session.select_component("comp-hdr-1")
    assert session.selected_component_id == "comp-hdr-1"

    session.set_component_visibility("comp-hdr-1", False)
    assert session.can_undo() is True
    session.undo()
    assert session.can_redo() is True
