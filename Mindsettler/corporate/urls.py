from django.urls import path
from . import views

app_name = 'corporate'   # 🔥 THIS LINE WAS MISSING

urlpatterns = [
    path('', views.corporate_services, name='corporate_services'),
    path('request/', views.request_service, name='request_service'),
]
