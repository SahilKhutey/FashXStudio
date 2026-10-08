import hashlib, pathlib, subprocess, sys

apply = "--apply" in sys.argv
only = sys.argv[sys.argv.index("--only") + 1]
roots = [pathlib.Path("app"), pathlib.Path("api/app")]
dest = pathlib.Path("backend/fashx")

def git(*a):
    print("+ git", *a)
    if apply:
        subprocess.run(["git", *a], check=True)

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

if apply:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "__init__.py").touch()

blocked = False
for r in roots:
    files = subprocess.run(["git", "ls-files", r.as_posix()], capture_output=True, text=True).stdout.split("\n")
    for f in filter(None, files):
        p = pathlib.Path(f)
        rel = p.relative_to(r)
        if rel.parts[0].removesuffix(".py") != only:
            continue
        target = dest / rel
        if target.exists():
            if digest(target) == digest(p):
                git("rm", "-q", p.as_posix())
            else:
                print(f"CONFLICT (different content): {p} vs {target}")
                blocked = True
            continue
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
        git("mv", p.as_posix(), target.as_posix())
sys.exit(1 if blocked else 0)
