"""Clear all mood entries"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mindsettler.settings')
django.setup()

from users.models import MoodEntry
from django.contrib.auth.models import User

user = User.objects.first()
entries = MoodEntry.objects.filter(user=user)
print(f'Found {entries.count()} entries for user {user.username}')

for e in entries:
    print(f'  {e.date}: mood={e.mood_score}')

deleted = entries.delete()
print(f'Deleted {deleted[0]} entries')
