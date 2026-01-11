"""Create mood data directly"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mindsettler.settings')
django.setup()

from users.models import MoodEntry
from django.contrib.auth.models import User
from datetime import date, timedelta

# Clear existing
MoodEntry.objects.all().delete()

user = User.objects.get(username='hpv')
today = date.today()

# Create individual entries  
mood_scores = [7, 6, 8, 5, 7, 9, 6, 8, 7, 5, 8, 6, 7, 8, 9, 7, 6, 8, 7, 8, 6, 7, 9, 8, 7, 6, 8, 7, 8, 6]

for i, score in enumerate(mood_scores):
    entry_date = today - timedelta(days=29-i)
    try:
        entry, created = MoodEntry.objects.update_or_create(
            user=user,
            date=entry_date,
            defaults={
                'mood_score': score,
                'note': f"Mood entry for {entry_date}"
            }
        )
        status = "Created" if created else "Updated"
        print(f"{status} {entry_date}: {score}/10")
    except Exception as e:
        print(f"Error for {entry_date}: {e}")

print(f"\nTotal: {MoodEntry.objects.filter(user=user).count()} entries")
