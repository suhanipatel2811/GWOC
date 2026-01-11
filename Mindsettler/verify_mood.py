"""Verify mood entries"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mindsettler.settings')
django.setup()

from users.models import MoodEntry
from django.contrib.auth.models import User

user = User.objects.get(username='hpv')
entries = MoodEntry.objects.filter(user=user).order_by('date')
print(f'Found {entries.count()} mood entries for {user.username}:')
for e in entries:
    print(f'  {e.date}: {e.mood_score}/10')
