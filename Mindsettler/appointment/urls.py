from django.urls import path
from . import views

app_name = 'appointment'

urlpatterns = [
    path('booking/', views.booking, name='booking'),
    path('available-slots/', views.available_slots, name='available_slots'),
    path('payment/<int:appointment_id>/', views.payment, name='payment'),
    path('confirm-payment/<int:appointment_id>/', views.confirm_payment, name='confirm_payment'),
    path('payment-success/<int:appointment_id>/', views.payment_success, name='payment_success'),
    path('payment-cancel/<int:appointment_id>/', views.payment_cancel, name='payment_cancel'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('confnotpay/', views.confnotpay, name='confnotpay'),
    path('download-ics/<int:appointment_id>/', views.download_ics, name='download_ics'),
    path('status/', views.appointment_status, name='status'),
    path('reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('journal/', views.journal, name='journal'),
    path('myjourney/', views.myjourney, name='myjourney'),
    path('specialists/', views.specialists, name='specialists'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('cancel/confirm/<int:appointment_id>/', views.confirm_cancellation, name='confirm_cancellation'),
]