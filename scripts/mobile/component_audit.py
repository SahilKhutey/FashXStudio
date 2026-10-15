import csv
import os
import re
import subprocess
from collections import defaultdict
from typing import TypedDict


class AuditRow(TypedDict):
    File: str
    Group: str
    Lines: int
    A11y: int
    UsesTokens: bool
    HardText: int
    MockData: bool
    FrozenWords: bool


class GroupSummary(TypedDict):
    Group: str
    Files: int
    Lines: int
    NoA11y: int
    Mock: int
    HardText: int


# Find all tsx/ts files in mobile/features excluding index.ts
git_files = subprocess.check_output(
    ["git", "ls-files", "mobile/features"], text=True
).splitlines()
files = [
    f
    for f in git_files
    if (f.endswith(".ts") or f.endswith(".tsx")) and not f.endswith("index.ts")
]

rows: list[AuditRow] = []
for f in files:
    if not os.path.isfile(f):
        continue
    with open(f, encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    parts = f.replace("\\", "/").split("/")
    # Group: if under mobile/features/visual/<group>, group is parts[3], else parts[2]
    if len(parts) > 3 and parts[2] == "visual":
        group = parts[3]
    elif len(parts) > 2:
        group = parts[2]
    else:
        group = "root"

    lines = len(text.splitlines())
    a11y = len(re.findall(r"accessibility(Label|Role|State|Hint)", text))
    uses_tokens = bool(re.search(r"tokens|useTheme|theme\.", text))
    hard_text = len(re.findall(r">\s*[A-Z][A-Za-z ,.'!?-]{3,}\s*<", text))
    mock_data = bool(re.search(r"mock|lorem|faker|MOCK_|sampleData", text, re.I))
    frozen_words = bool(re.search(r"cart|checkout|payment|shipping", text, re.I))

    rows.append(
        {
            "File": f,
            "Group": group,
            "Lines": lines,
            "A11y": a11y,
            "UsesTokens": uses_tokens,
            "HardText": hard_text,
            "MockData": mock_data,
            "FrozenWords": frozen_words,
        }
    )

# Write CSV
csv_fields = [
    "File",
    "Group",
    "Lines",
    "A11y",
    "UsesTokens",
    "HardText",
    "MockData",
    "FrozenWords",
]
with open(
    "mobile-component-audit.csv", "w", newline="", encoding="utf-8"
) as fh:
    writer = csv.DictWriter(fh, fieldnames=csv_fields)
    writer.writeheader()
    writer.writerows(rows)

# Group Summary
groups: defaultdict[str, list[AuditRow]] = defaultdict(list)
for r in rows:
    groups[r["Group"]].append(r)

summary: list[GroupSummary] = []
for grp, items in sorted(groups.items()):
    total_lines = sum(i["Lines"] for i in items)
    no_a11y = sum(1 for i in items if i["A11y"] == 0)
    mock_count = sum(1 for i in items if i["MockData"])
    hard_text_sum = sum(i["HardText"] for i in items)
    summary.append(
        {
            "Group": grp,
            "Files": len(items),
            "Lines": total_lines,
            "NoA11y": no_a11y,
            "Mock": mock_count,
            "HardText": hard_text_sum,
        }
    )

print(
    f"{'Group':<15} {'Files':<8} {'Lines':<8} {'NoA11y':<8} {'Mock':<8} {'HardText':<8}"
)
print("-" * 55)
for s in summary:
    print(
        f"{s['Group']:<15} {s['Files']:<8} {s['Lines']:<8} {s['NoA11y']:<8} {s['Mock']:<8} {s['HardText']:<8}"
    )
print("-" * 55)
total_files = len(rows)
total_lines = sum(s["Lines"] for s in summary)
print(f"{'TOTAL':<15} {total_files:<8} {total_lines:<8}")
