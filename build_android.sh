#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install --user --upgrade buildozer cython virtualenv
buildozer android debug
