from django.urls import path
from . import views

app_name = 'appointment'

urlpatterns = [
    path('booking/', views.booking, name='booking'),
    path('payment-success/<int:appointment_id>/', views.payment_success, name='payment_success'),
    path('payment-cancel/<int:appointment_id>/', views.payment_cancel, name='payment_cancel'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('download-ics/<int:appointment_id>/', views.download_ics, name='download_ics'),
    path('status/', views.appointment_status, name='status'),
    path('reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('cancel/confirm/<int:appointment_id>/', views.confirm_cancellation, name='confirm_cancellation'),
]