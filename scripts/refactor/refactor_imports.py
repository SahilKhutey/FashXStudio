import pathlib, re, subprocess, sys

apply = "--apply" in sys.argv
name = sys.argv[1]
SKIP_DIRS = ("docs/", "backend/fashx/frozen_never/", "apps/")
EXTS = (".py", ".ini", ".toml", ".yml", ".yaml", ".cfg", ".sh", ".ps1")
NAMES = ("Makefile", "Dockerfile")
RISKY = {"state", "router", "routes", "middleware", "extra", "get", "post", "put", "delete", "mount", "title", "version", "debug"}
if name in RISKY:
    print(f"WARNING: '{name}' collides with FastAPI attribute names; review diffs carefully")

# app.<name> or api.app.<name> -> fashx.<name>
pat = re.compile(rf"(?<![\w.])(?:api\.)?app(?=\.{re.escape(name)}\b)")
# from app import <name>  /  from api.app import <name>
pat2 = re.compile(rf"(?<![\w.])from\s+(?:api\.)?app\s+import\s+{re.escape(name)}\b")
# from .{name} or from ..{name} -> from fashx.{name}
pat3 = re.compile(rf"(?<![\w.])from\s+\.{1,2}{re.escape(name)}\b")

files = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split("\n")
changed = 0
for f in filter(None, files):
    p = pathlib.Path(f)
    if f.startswith(SKIP_DIRS) or not (f.endswith(EXTS) or p.name in NAMES):
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        continue
    new = pat.sub("fashx", text)
    new = pat2.sub(f"from fashx import {name}", new)
    new = pat3.sub(f"from fashx.{name}", new)
    if new != text:
        changed += 1
        print(f"rewrite: {f}")
        if apply:
            p.write_text(new, encoding="utf-8", newline="\n")
print(f"{changed} files {'changed' if apply else 'would change'} for '{name}'")
