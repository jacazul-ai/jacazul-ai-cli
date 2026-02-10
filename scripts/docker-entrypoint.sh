#!/bin/bash
set -e

# # Initialize Python venv if it doesn't exist
# if [ ! -f "/project/sandbox/venv/bin/python3" ]; then
#     echo "🐍 Initializing Python venv at /project/sandbox/venv..."
#     python3 -m venv /project/sandbox/venv
#     echo "✅ Venv created successfully"
# fi

# Pass control to the main command (copilot CLI)
exec "$@"
