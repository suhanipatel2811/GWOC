from django.db import models
from datetime import time

class SessionSlot(models.Model):
    date = models.DateField()
    time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('date', 'time')
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.date} | {self.time.strftime('%I:%M %p')}"

class Appointment(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    slot = models.ForeignKey(SessionSlot, on_delete=models.PROTECT, related_name="appointments")
    booked_on = models.DateTimeField(auto_now_add=True)

    # Session info
    SESSION_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline (Studio)')
    ]
    session_type = models.CharField(max_length=10, choices=SESSION_CHOICES, default='ONLINE')
    duration_minutes = models.PositiveIntegerField(default=60)
    first_session = models.BooleanField(default=False)

    # Scheduling / status
    STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    # Payment (no gateway). Manual confirmation expected.
    PAYMENT_MODES = [
        ('UPI', 'UPI'),
        ('CASH', 'Cash')
    ]
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default='UPI')
    upi_id = models.CharField(max_length=100, blank=True, help_text='UPI ID to send payment to (if applicable)')
    payment_confirmed = models.BooleanField(default=False)

    # Optional location / calendar
    location_details = models.CharField(max_length=255, blank=True, help_text='Studio address or online meeting link')
    add_to_google_calendar = models.BooleanField(default=False)
    google_calendar_link = models.URLField(blank=True, null=True)

    stripe_session_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-booked_on']

    def __str__(self):
        return f"{self.full_name} → {self.slot}"
