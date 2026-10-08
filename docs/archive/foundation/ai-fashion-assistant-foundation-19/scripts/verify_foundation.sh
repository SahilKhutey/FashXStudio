#!/usr/bin/env bash
set -euo pipefail

python -m compileall -q api schemas database tests
pytest -q
