from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('like/<slug:slug>/', views.like_article, name='like_article'),

]
