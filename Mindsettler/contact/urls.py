from django.urls import path
from .views import chatbot_api, contact_view, chatbot_view

app_name = 'contact'

urlpatterns = [
    path('', contact_view, name='contact'),
    path('chatbot/', chatbot_view, name='chatbot'),
    path("chatbot/api/", chatbot_api, name="chatbot_api"),

]
