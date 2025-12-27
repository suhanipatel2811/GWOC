from django.contrib import admin
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
        'payment_status',
    )
    list_filter = ('payment_status',)

    def get_slot(self, obj):
        return f"{obj.slot.date} {obj.slot.time.strftime('%I:%M %p')}"
    get_slot.short_description = 'Slot'
