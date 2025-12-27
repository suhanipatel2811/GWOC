from django.contrib import admin
from .models import CorporateServiceRequest

@admin.register(CorporateServiceRequest)
class CorporateServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'service_type',
        'number_of_employees',
        'preferred_date',
        'created_at'
    )
    list_filter = ('service_type', 'preferred_date')
    search_fields = ('company_name', 'email')
    ordering = ('-created_at',)