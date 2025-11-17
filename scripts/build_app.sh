#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# Build single-file CLI app
pyinstaller --noconfirm -F -n pqc_qkd_cli scripts/cli_entry.py \
  --paths . \
  --hidden-import qkdn_sim
echo "Built at dist/pqc_qkd_cli"

# Build windowed GUI app
pyinstaller --noconfirm -w -n "PQC-QKD Suite GUI" scripts/gui_entry.py \
  --paths . \
  --hidden-import qkdn_sim
echo "Built GUI at dist/PQC-QKD Suite GUI.app"
