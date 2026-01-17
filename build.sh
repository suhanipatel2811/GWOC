#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Navigate to Django project directory
cd Mindsettler

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
