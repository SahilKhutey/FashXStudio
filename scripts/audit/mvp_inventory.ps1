$o = [System.Collections.Generic.List[string]]::new(); function Say($s) { $o.Add([string]$s) }
git fetch --all --prune --tags 2>$null | Out-Null
Say "# MVP inventory $(Get-Date -Format s)"; Say ("current branch: " + (git rev-parse --abbrev-ref HEAD))

Say "`n## Remote branches vs origin/main"
git for-each-ref --format="%(refname:short)|%(committerdate:short)" refs/remotes/origin | ForEach-Object {
  $r, $d = $_ -split "\|"; if ($r -in "origin", "origin/HEAD", "origin/main") { return }
  $lr = (git rev-list --left-right --count "origin/main...$r") -split "\s+"
  Say ("{0,-58} {1}  ahead={2} behind={3}" -f $r, $d, $lr[1], $lr[0]) }
Say ("tags: " + ((git tag --list) -join ", "))

Say "`n## Pull requests and CI"
try { gh pr list --state all --limit 15 | ForEach-Object { Say $_ }; gh run list --limit 10 | ForEach-Object { Say $_ } } catch { Say "gh not available or not logged in" }

Say "`n## Backend"
Say ("alembic heads: " + ((python -m alembic heads 2>&1) -join " "))
Say ("tests collected: " + ((python -m pytest tests --collect-only -q -p no:cacheprovider 2>&1 | Select-Object -Last 1)))
Say ("skip/xfail markers: " + (git grep -c -E "pytest\.mark\.(skip|xfail)|pytest\.skip\(" -- tests | Measure-Object).Count + " files")
Say ("continue-on-error / '|| true' in workflows: " + (git grep -c -E "continue-on-error|\|\| true" -- .github | Measure-Object).Count + " files")
Say "routes:"
python -c "from fashx.main import app; print('\n'.join(sorted(f'{m} {r.path}' for r in app.routes if hasattr(r,'methods') for m in r.methods if m not in ('HEAD','OPTIONS'))))" 2>&1 | ForEach-Object { Say ("  " + $_) }
Say "B2B / frozen wiring in main.py:"; git grep -n -E "tenant|widget|FASHX_ENABLE_FROZEN|feature_flag" -- backend/fashx/main.py | ForEach-Object { Say ("  " + $_) }
Say "try-on adapters:"; git grep -n -E "class \w*Adapter|TRYON_PROVIDER|tryon_provider" -- backend ml | Select-Object -First 15 | ForEach-Object { Say ("  " + $_) }
Say "embedder:"; git grep -n -i -E "embedding=|embed_images|MarqoFashion" -- backend | Select-Object -First 8 | ForEach-Object { Say ("  " + $_) }

Say "`n## Mobile"
Say "screens:"; git ls-files mobile/app | ForEach-Object { Say ("  " + $_) }
Say "API calls from the app:"; git grep -n -E "api(<|\()" -- mobile/src mobile/app | Select-Object -First 60 | ForEach-Object { Say ("  " + $_) }
Say ("jest tests: " + (git ls-files mobile/__tests__ | Measure-Object).Count + " files")

Say "`n## Repo hygiene"
Say ("files tracked: " + (git ls-files | Measure-Object).Count)
Say ("docs/evidence cards: " + ((git ls-files docs/evidence) -join ", "))
Say ("Docker: " + $(if (Get-Command docker -ErrorAction SilentlyContinue) { "installed" } else { "NOT installed" }))
Say ("catalog_seed images: " + $(if (Test-Path catalog_seed/images) { (Get-ChildItem catalog_seed/images).Count } else { 0 }))
Say ("AGENTS.md: " + (Test-Path AGENTS.md)); Say ("lock files: " + ((git ls-files | Select-String -Pattern "(poetry|uv)\.lock|requirements.*\.txt|package-lock\.json") -join ", "))
$o | Set-Content mvp-inventory.md -Encoding utf8; "wrote mvp-inventory.md"
