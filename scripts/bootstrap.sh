#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.11)"
elif [[ -x "/opt/homebrew/bin/python3.11" ]]; then
  PYTHON_BIN="/opt/homebrew/bin/python3.11"
else
  echo "Python 3.11 is required but was not found."
  echo "Install it with: brew install python@3.11"
  exit 1
fi

echo "Using Python: $PYTHON_BIN"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
pip install -r "$ROOT_DIR/api/requirements.txt"
pip install -r "$ROOT_DIR/app/requirements.txt"

echo "Setup complete."
echo "Start backend:  cd api && source ../.venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo "Start frontend: cd app && source ../.venv/bin/activate && streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0"
