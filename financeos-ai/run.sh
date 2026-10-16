#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Create the environment first: python3 -m venv .venv'
  echo 'Then install dependencies: .venv/bin/python -m pip install -r requirements.txt'
  exit 1
fi
exec .venv/bin/python -m uvicorn financeos.main:app --host 127.0.0.1 --port "${PORT:-8000}"
