#!/usr/bin/env bash
set -e
"$(dirname "$0")/stop.sh"
"$(dirname "$0")/start.sh"
