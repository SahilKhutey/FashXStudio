# READ-ONLY.  Usage: .\scripts\audit\mvp_full_audit.ps1 [-RunTests] [-RunMobile]
param([switch]$RunTests, [switch]$RunMobile)
$ErrorActionPreference = "Continue"
Remove-Item Alias:\h -Force -ErrorAction SilentlyContinue
$py = if (Test-Path .\.venv\Scripts\python.exe) { ".\.venv\Scripts\python.exe" } else { "python" }
$o = [System.Collections.Generic.List[string]]::new()
function H($t) { Write-Host "## $t"; $o.Add("`n## $t") }
function L($s) { $o.Add([string]$s) }
function Cap([scriptblock]$b) { try { (& $b 2>&1 | Out-String).Trim() } catch { "ERROR: $_" } }
function Lines($s, $prefix = "  ") { ($s -split "`r?`n") | Where-Object { $_ } | ForEach-Object { L ($prefix + $_) } }
function Cnt($pat, $paths) { (git grep -c -E $pat -- $paths 2>$null | ForEach-Object { [int](($_ -split ":")[-1]) } | Measure-Object -Sum).Sum + 0 }

L "# MVP full audit $(Get-Date -Format s)"
H "0. Environment"
L ("python: " + (Cap { & $py --version }) + " | interpreter: $py | .venv present: " + (Test-Path .\.venv))
L ("node: " + (Cap { node --version }) + " | npm: " + (Cap { npm --version }))
L ("docker: " + $(if (Get-Command docker -ErrorAction SilentlyContinue) { Cap { docker --version } } else { "NOT installed" }))
L ("gh: " + $(if (Get-Command gh -ErrorAction SilentlyContinue) { ((Cap { gh auth status }) -replace "\s+", " ") } else { "NOT installed" }))
L ("TEST_DATABASE_URL set: " + [bool]$env:TEST_DATABASE_URL)

H "1. Git"
git fetch --all --prune --tags 2>$null | Out-Null
L ("branch: " + (git rev-parse --abbrev-ref HEAD) + " | HEAD: " + (git rev-parse --short HEAD))
L ("local main vs origin/main (behind ahead): " + (git rev-list --left-right --count origin/main...main 2>$null))
L "uncommitted changes:"; Lines (Cap { git status --short })
L "remote branches vs origin/main:"
git for-each-ref --format="%(refname:short)|%(committerdate:short)|%(authorname)|%(subject)" refs/remotes/origin | ForEach-Object {
  $r, $d, $a, $s = $_ -split "\|", 4
  if ($r -in "origin", "origin/HEAD", "origin/main") { return }
  $lr = (git rev-list --left-right --count "origin/main...$r") -split "\s+"
  $stat = if ([int]$lr[1] -gt 0) { (git diff --shortstat "origin/main...$r") -replace "^\s+", "" } else { "" }
  L ("  {0,-52} {1} ahead={2} behind={3}  {4}" -f $r, $d, $lr[1], $lr[0], $stat) }
L "tags:"; Lines (Cap { git for-each-ref --sort=-creatordate refs/tags --format="%(refname:short) %(objectname:short) %(creatordate:short)" })
L "local branches:"; Lines (Cap { git branch -vv })
L "stashes:"; Lines (Cap { git stash list })

H "2. GitHub: pull requests and CI"
gh auth status >$null 2>&1
$ghOk = (Get-Command gh -ErrorAction SilentlyContinue) -and ($LASTEXITCODE -eq 0)
if ($ghOk) {
  L "PRs:"; Lines (Cap { gh pr list --state all --limit 20 })
  L "recent runs:"; Lines (Cap { gh run list --limit 15 })
  foreach ($b in "main", "fix/ci-main") {
    $r = (Cap { gh run list --branch $b --limit 1 --json databaseId,conclusion,headSha }) | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($r) { L "latest run on ${b}: id $($r[0].databaseId) conclusion '$($r[0].conclusion)' commit $($r[0].headSha.Substring(0,7))"
      $j = (Cap { gh run view $r[0].databaseId --json jobs }) | ConvertFrom-Json -ErrorAction SilentlyContinue
      foreach ($job in $j.jobs) { L "    $($job.name): $($job.conclusion)"
        foreach ($st in $job.steps) { if ($st.conclusion -eq "failure") { L "        failed step: $($st.name)" } } } } }
} else { L "gh not available: read the Actions tab manually" }

H "3. Files"
$files = @(git ls-files)
L ("tracked files: " + $files.Count)
$files | Group-Object { ($_ -split "/")[0] } | Sort-Object Count -Descending | Select-Object -First 25 | ForEach-Object { L ("  {0,-24} {1}" -f $_.Name, $_.Count) }
L "tracked files over 1 MB:"
$files | ForEach-Object { Get-Item $_ -ErrorAction SilentlyContinue } | Where-Object { $_.Length -gt 1MB } | Sort-Object Length -Descending | Select-Object -First 10 | ForEach-Object { L ("  {0:N1} MB  {1}" -f ($_.Length / 1MB), $_.Name) }
L ("evidence cards: " + (($files | Where-Object { $_ -like "docs/evidence/*" }) -join ", "))
L ("docs/_simulated files: " + @($files | Where-Object { $_ -like "docs/_simulated/*" }).Count)
L ("catalog_seed images on disk: " + $(if (Test-Path catalog_seed/images) { @(Get-ChildItem catalog_seed/images).Count } else { 0 }))

H "4. Backend"
L ("alembic heads: " + (Cap { & $py -m alembic heads }))
L ("migration files: " + @($files | Where-Object { $_ -match "migrations/versions/.*\.py$" }).Count)
Cap { & $py -c "import json; from fashx.main import app; json.dump(app.openapi(), open('openapi.audit.json','w'))" } | Out-Null
$spec = $null; if (Test-Path openapi.audit.json) { $spec = Get-Content openapi.audit.json -Raw | ConvertFrom-Json }
$paths = @(); if ($spec) { $paths = @($spec.paths.PSObject.Properties.Name); L ("openapi paths: " + $paths.Count)
  L "paths matching frozen / B2B patterns (must be none):"
  $paths | Where-Object { $_ -match "cart|checkout|payment|order|inventory|promotion|fulfil|return|widget|tenant" } | ForEach-Object { L "  $_" } } else { L "could not import fashx.main to read OpenAPI" }
L "try-on adapters:"; git grep -n -E "class \w*Adapter|tryon_provider" -- backend ml | Select-Object -First 12 | ForEach-Object { L "  $_" }
L ("research-model references outside docs: " + (git grep -n -i -E "idm-vton|catvton|ootdiffusion|research_diffusion" -- . ":!docs" 2>$null | Measure-Object).Count)
L "constant embeddings:"; git grep -n -E "\[0\.0?5\] \* 512" -- backend | ForEach-Object { L "  $_" }
L "dev-files route:"; git grep -n "dev-files" -- backend | Select-Object -First 6 | ForEach-Object { L "  $_" }
L ("noqa: " + (Cnt "# noqa" "*.py") + " | type: ignore: " + (Cnt "# type: ignore" "*.py") + " | skip/xfail: " + (Cnt "pytest\.mark\.(skip|xfail)|pytest\.skip\(" "tests") + " | TODO/FIXME/HACK in backend: " + (Cnt "TODO|FIXME|HACK" "backend") + " | 'mock' in backend: " + (Cnt "[Mm]ock" "backend"))
foreach ($m in @("", "-m db", "-m frozen")) { L ("tests collected [$m]: " + (((Cap { & $py -m pytest tests --collect-only -q -p no:cacheprovider $m.Split(" ") }) -split "`n")[-1])) }
if ($RunTests) {
  Write-Host "Running pytest (not frozen, not db) - approx 4 minutes..."
  L "pytest (not frozen, not db):"; Lines (((Cap { & $py -m pytest tests -q -p no:cacheprovider -m "not frozen and not db" }) -split "`n") | Select-Object -Last 6)
  Write-Host "Running ruff check..."
  L "ruff:"; Lines (Cap { & $py -m ruff check . })
  Write-Host "Running mypy..."
  L "mypy:"; Lines (((Cap { & $py -m mypy . }) -split "`n") | Select-Object -Last 3)
  if ($env:TEST_DATABASE_URL) { L "db tests:"; Lines (((Cap { & $py -m pytest tests -m db -q -rs -p no:cacheprovider }) -split "`n") | Select-Object -Last 8) } else { L "db tests NOT RUN: no TEST_DATABASE_URL" } }

H "5. Mobile"
L "screens:"; $files | Where-Object { $_ -like "mobile/app/*" } | ForEach-Object { L "  $_" }
L ("jest test files: " + @($files | Where-Object { $_ -like "mobile/__tests__/*" }).Count)
$calls = Get-ChildItem mobile/src, mobile/app -Recurse -Include *.ts, *.tsx -ErrorAction SilentlyContinue |
  Select-String -Pattern 'api(?:<[^>]*>)?\(\s*["''`]([^"''`$]+)' | ForEach-Object { $_.Matches[0].Groups[1].Value.Split("?")[0] } | Sort-Object -Unique
L ("distinct API paths called by the app: " + @($calls).Count)
if ($spec) { foreach ($c in $calls) { $p = $c.TrimEnd("/"); $hit = @($paths | Where-Object { $_ -like "/api/v1$p*" }); if ($hit.Count -eq 0) { L "  APP CALLS A PATH THE BACKEND DOES NOT HAVE: $c" } } }
if ($RunMobile) { Push-Location mobile
  foreach ($cmd in @("npx tsc --noEmit", "npx eslint . --max-warnings 0", "npx jest --ci", "npx expo-doctor")) {
    Write-Host "Running mobile: $cmd..."
    L "> $cmd"; Lines (((Cap { Invoke-Expression $cmd }) -split "`n") | Select-Object -Last 6)
  }
  Pop-Location }

H "6. Config"
$envKeys = @(Select-String -Path .env.example -Pattern '^([A-Z][A-Z0-9_]+)=' | ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique)
$codeKeys = @(git grep -h -o -E 'validation_alias="[A-Z0-9_]+"' -- backend | ForEach-Object { ($_ -split '"')[1] } | Sort-Object -Unique)
L ("keys read by code but missing from .env.example: " + (($codeKeys | Where-Object { $_ -notin $envKeys }) -join ", "))

H "7. CI configuration"
$files | Where-Object { $_ -like ".github/workflows/*" } | ForEach-Object { L "  $_" }
L "continue-on-error / '|| true':"; git grep -n -E "continue-on-error|\|\| true" -- .github | ForEach-Object { L "  $_" }
L ("TEST_DATABASE_URL referenced in workflows: " + (Cnt "TEST_DATABASE_URL" ".github"))
L "branch protection: check Settings > Rules (not readable here)"

H "8. Docs and claims"
if (Test-Path docs/STATUS.md) { L ("check marks in STATUS.md: " + @(Select-String -Path docs/STATUS.md -Pattern "✅").Count); L "STATUS.md head:"; Get-Content docs/STATUS.md -TotalCount 30 | ForEach-Object { L "  $_" } }
L ("docs lint: " + (Cap { & $py scripts/docs_lint.py }))
L ("'cleared|verified|passed' lines in docs outside _simulated: " + (git grep -c -i -E "cleared|verified|passed" -- docs ":!docs/_simulated" 2>$null | Measure-Object).Count + " file(s)")
if (Get-Command gitleaks -ErrorAction SilentlyContinue) { L "gitleaks (all refs):"; Lines (((Cap { gitleaks detect --log-opts="--all" --redact --no-banner }) -split "`n") | Select-Object -Last 3) } else { L "gitleaks not installed" }
$o | Set-Content mvp-audit.md -Encoding utf8; "wrote mvp-audit.md"
