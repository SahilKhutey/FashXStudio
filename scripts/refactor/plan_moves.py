import collections, hashlib, pathlib, subprocess

def tracked(root):
    out = subprocess.run(["git", "ls-files", root], capture_output=True, text=True).stdout.split("\n")
    return [pathlib.Path(p) for p in out if p.endswith(".py")]

roots = [pathlib.Path("app"), pathlib.Path("api/app")]
seen = collections.defaultdict(list)
for r in roots:
    for p in tracked(r.as_posix()):
        seen[p.relative_to(r).as_posix()].append(p)

print(f"{len(seen)} distinct module paths")
for r in roots:
    print(f"{r}/__init__.py exists:", (r / "__init__.py").exists())

conflicts = {k: v for k, v in seen.items() if len(v) > 1}
print(f"\nCONFLICTS (same path in both trees): {len(conflicts)}")
for k, v in sorted(conflicts.items()):
    same = len({hashlib.sha256(p.read_bytes()).hexdigest() for p in v}) == 1
    print(f"  {k}: {'identical' if same else 'DIFFERENT -> merge by hand'}")

tops = sorted({k.split("/")[0].removesuffix(".py") for k in seen})
print("\nTOP-LEVEL NAMES:", ",".join(tops))
for r in roots:
    print(f"{r}:", sorted({p.relative_to(r).parts[0].removesuffix('.py') for p in tracked(r.as_posix())}))
