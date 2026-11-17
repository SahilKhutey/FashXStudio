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
                ok |= (
                    bool(re.search(r"^evidence:\s*real\s*$", head, re.M))
                    and "collected_by:" in head
                    and "raw_data:" in head
                )
        if not ok:
            errors.append(f"STATUS.md:{i}: ✅ needs a link to a real evidence card")

evidence_dir = ROOT / "docs/evidence"
if evidence_dir.exists():
    for p in evidence_dir.glob("*.md"):
        if p.name == "README.md":
            continue
        text = p.read_text(encoding="utf-8")[:500]
        has_collected_by = bool(re.search(r"^collected_by:\s*.+", text, re.M))
        has_raw_data = bool(re.search(r"^raw_data:\s*.+", text, re.M))
        if not (has_collected_by and has_raw_data):
            errors.append(f"{p}: missing collected_by or raw_data in frontmatter")

# Engineering standards validation (Phase 2.6)
REQUIRED_ENGINEERING_DOCS = [
    "ENGINEERING_STANDARDS.md",
    "BRANCHING_AND_COMMITS.md",
    "PULL_REQUEST_STANDARD.md",
    "CODE_REVIEW_CHECKLIST.md",
    "TESTING_STANDARD.md",
    "API_VERSIONING_STANDARD.md",
    "DATABASE_MIGRATION_STANDARD.md",
    "LOGGING_STANDARD.md",
    "ERROR_HANDLING_STANDARD.md",
    "ENVIRONMENT_CONFIGURATION_STANDARD.md",
    "DEPENDENCY_MANAGEMENT_STANDARD.md",
    "FEATURE_FLAG_STANDARD.md",
]

eng_dir = ROOT / "docs/engineering"
if eng_dir.exists():
    for doc in REQUIRED_ENGINEERING_DOCS:
        p = eng_dir / doc
        if not p.exists():
            errors.append(f"docs/engineering: missing required standards document {doc}")
        elif p.stat().st_size < 100:
            errors.append(f"docs/engineering/{doc}: file is empty or suspiciously short")
        else:
            # Check relative markdown links inside engineering docs
            text = p.read_text(encoding="utf-8")
            for link in re.findall(r"\[.*?\]\(([^)#:]+\.md)\)", text):
                target = (p.parent / link).resolve()
                if not target.exists():
                    errors.append(f"docs/engineering/{doc}: broken relative link to {link}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print("docs lint ok")
sys.exit(0)
