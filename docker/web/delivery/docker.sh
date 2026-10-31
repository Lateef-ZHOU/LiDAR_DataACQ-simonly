#!/usr/bin/env bash
# Run Docker as the current user when possible, otherwise use sudo.
set -euo pipefail
if docker info >/dev/null 2>&1; then
    exec docker "$@"
else
    exec sudo docker "$@"
fi
