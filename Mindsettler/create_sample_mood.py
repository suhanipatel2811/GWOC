"""
Create sample mood entries for testing the mood graph.
Run this script from the Django shell or as a management command.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mindsettler.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import MoodEntry
from datetime import date, timedelta
import random

# Get the first user (or specify username)
user = User.objects.first()

if not user:
    print("No users found. Please create a user first.")
else:
    print(f"Creating mood entries for user: {user.username}")
    
    # Create mood entries for the last 30 days
    today = date.today()
    
    # Create all entries at once using bulk_create
    entries_to_create = []
    for i in range(30):
        entry_date = today - timedelta(days=i)
        # Generate realistic mood scores (slightly positive bias)
        mood_score = random.choice([4, 5, 6, 7, 8, 8, 9])
        
        entries_to_create.append(
            MoodEntry(
                user=user,
                date=entry_date,
                mood_score=mood_score,
                note=f"Sample mood entry for {entry_date}"
            )
        )
    
    # Bulk create all entries
    created = MoodEntry.objects.bulk_create(entries_to_create, ignore_conflicts=True)
    print(f"\nCreated {len(created)} mood entries!")
    print(f"Total mood entries for {user.username}: {MoodEntry.objects.filter(user=user).count()}")
