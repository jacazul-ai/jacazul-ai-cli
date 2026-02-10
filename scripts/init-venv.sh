#!/bin/bash
# Initialize Python venv and install dependencies

VENV_PATH="/project/sandbox/venv"

# Check if venv is initialized
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "🐍 Initializing Python virtual environment..."
    python3 -m venv "$VENV_PATH"
    
    # Install orjson
    echo "📦 Installing orjson..."
    "$VENV_PATH/bin/pip" install --quiet orjson
    
    echo "✅ Python environment ready at $VENV_PATH"
else
    echo "✅ Python venv already initialized"
fi
