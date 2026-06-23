#!/usr/bin/env sh
set -eu
"$(dirname "$0")/stop.sh"
"$(dirname "$0")/start.sh"

