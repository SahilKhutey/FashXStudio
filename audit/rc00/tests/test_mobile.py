import json
from pathlib import Path
from audit.rc00.mobile_audit import audit_mobile


def test_mobile_package_detected(tmp_path: Path):
    mobile = tmp_path / "mobile"
    mobile.mkdir()
    package = {
        "dependencies": {
            "expo": "~57.0.31",
            "expo-router": "~57.0.29",
            "react": "19.2.3",
            "react-native": "0.86.3",
            "@tanstack/react-query": "^5.89.0",
            "zustand": "^5.0.8",
            "zod": "^4.6.5",
        },
        "scripts": {
            "start": "expo start",
            "test": "jest",
            "typecheck": "tsc --noEmit",
        },
    }
    (mobile / "package.json").write_text(json.dumps(package), encoding="utf-8")
    result = audit_mobile(tmp_path)
    assert result["package_exists"] is True
    assert result["missing_dependencies"] == []
