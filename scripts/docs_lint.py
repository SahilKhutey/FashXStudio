import pathlib
import re
import sys

ROOT = pathlib.Path(".")
errors = []
status_path = ROOT / "docs/STATUS.md"
if not status_path.exists():
    print("ERROR: docs/STATUS.md not found")
    sys.exit(1)

for i, line in enumerate(status_path.read_text(encoding="utf-8").splitlines(), 1):
    if line.lstrip().startswith("|") and "✅" in line:
        ok = False
        for link in re.findall(r"\]\(([^)#]+\.md)", line):
            p = (ROOT / "docs" / link).resolve()
            if p.exists() and "_simulated" not in p.parts:
                head = p.read_text(encoding="utf-8")[:400]
                ok |= bool(re.search(r"^evidence:\s*real\s*$", head, re.M)) and "collected_by:" in head
        if not ok:
            errors.append(f"STATUS.md:{i}: ✅ needs a link to a real evidence card")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print("docs lint ok")
sys.exit(0)
