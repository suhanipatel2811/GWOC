from django.contrib import admin, messages
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import quote

from .models import SessionSlot, Appointment

@admin.register(SessionSlot)
class SessionSlotAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'is_available')
    list_filter = ('date', 'is_available')
    list_editable = ('is_available',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'email',
        'phone',
        'get_slot',
        'status',
        'payment_mode',
        'payment_confirmed',
    )
    list_filter = ('status', 'payment_mode', 'payment_confirmed')

    def get_slot(self, obj):
        return f"{obj.slot.date} {obj.slot.time.strftime('%I:%M %p')}"
    get_slot.short_description = 'Slot'

    actions = ['confirm_payment']

    def confirm_payment(self, request, queryset):
        """Admin action to mark payment confirmed and confirm booking."""
        updated = 0
        for appointment in queryset:
            appointment.payment_confirmed = True
            appointment.status = 'CONFIRMED'

            # lock the slot (ensure unavailable)
            slot = getattr(appointment, 'slot', None)
            if slot:
                slot.is_available = False
                slot.save()

            # generate a simple Google Calendar add link if requested and missing
            if appointment.add_to_google_calendar and not appointment.google_calendar_link and slot:
                try:
                    start_dt = timezone.make_aware(datetime.combine(slot.date, slot.time))
                except Exception:
                    start_dt = datetime.combine(slot.date, slot.time)
                    start_dt = timezone.make_aware(start_dt)

                end_dt = start_dt + timedelta(minutes=appointment.duration_minutes or 60)
                start_utc = start_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                end_utc = end_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')

                title = quote(f"MindSettler Session - {appointment.full_name}")
                details = quote("MindSettler consultation session")
                location = quote(appointment.location_details or "MindSettler Online / Studio")

                # add the appointment email as an attendee so the calendar event opens for that account
                try:
                    attendee = quote(appointment.email)
                except Exception:
                    attendee = ''

                add_param = f"&add=mailto:{attendee}" if attendee else ''

                gcal_url = (
                    "https://www.google.com/calendar/render?action=TEMPLATE"
                    f"&text={title}&dates={start_utc}/{end_utc}&details={details}&location={location}{add_param}"
                )
                appointment.google_calendar_link = gcal_url

            appointment.save()
            updated += 1

        self.message_user(request, f"Confirmed payment for {updated} appointment(s).", level=messages.SUCCESS)

    confirm_payment.short_description = 'Confirm payment & booking for selected appointments'
