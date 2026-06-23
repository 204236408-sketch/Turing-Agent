#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/../backend"
exec uvicorn main:app --host 0.0.0.0 --port 8000

