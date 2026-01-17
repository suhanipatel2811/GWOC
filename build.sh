#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Navigate to Django project directory
cd Mindsettler

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
