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

    payment_status = models.CharField(
        max_length=10,
        choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('FAILED', 'Failed')],
        default="PENDING"
    )

    stripe_session_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-booked_on']

    def __str__(self):
        return f"{self.full_name} → {self.slot}"
