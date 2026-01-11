from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True, unique=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_type = models.CharField(max_length=20, blank=True, null=True, 
                                   choices=[
                                       ('masculine', 'Masculine'),
                                       ('feminine', 'Feminine'),
                                       ('neutral', 'Neutral'),
                                       ('initials', 'Initials')
                                   ])
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    daily_reminder = models.BooleanField(default=True)
    public_profile = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Provide a temporary empty phone so creation doesn't fail on pre-migration DB schema
        Profile.objects.create(user=instance, phone='')

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


from django.contrib.auth.signals import user_logged_in


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} @ {self.timestamp}"


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    Activity.objects.create(user=user, action='login')


class MoodEntry(models.Model):
    """Track user's daily mood on a scale of 1-10."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood_score = models.IntegerField(choices=[(i, i) for i in range(1, 11)])  # 1-10 scale
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']  # One mood entry per day per user

    def __str__(self):
        return f"{self.user.username} - Mood: {self.mood_score}/10 on {self.date}"


class GoogleCalendarCredential(models.Model):
    """Store a user's Google OAuth2 credentials as JSON."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_credentials')
    credentials = models.TextField(blank=True, help_text='Serialized google.oauth2.credentials.Credentials.to_json()')
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Google credentials for {self.user.username}"