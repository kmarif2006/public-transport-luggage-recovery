#!/bin/bash
set -e

# Setup pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

cd ~/srm-project

echo "=== Checking pyenv versions ==="
pyenv versions

echo ""
echo "=== Setting Python 3.11.9 for this project ==="
pyenv local 3.11.9

echo ""
echo "=== Current Python version ==="
python --version

echo ""
echo "=== Creating virtual environment ==="
python -m venv venv

echo ""
echo "=== Activating venv and installing dependencies ==="
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo ""
echo "=== Setup complete! ==="
echo "To run the app:"
echo "  cd ~/srm-project"
echo "  source venv/bin/activate"
echo "  python app.py"

