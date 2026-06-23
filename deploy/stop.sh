#!/usr/bin/env sh
set -eu
pkill -f "uvicorn main:app" || true

