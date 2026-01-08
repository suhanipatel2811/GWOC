from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('base/', views.base, name='base'),
    path('about/', views.about, name='about'),
    path('psycho-education/', views.psycho_education, name='psycho_education'),
    path('what', views.what, name='what'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('journey/', views.journey, name='journey'),
    path('what_makes_us_different/', views.what_makes_us_different, name='what_makes_us_different'),
    path('book-session/', views.book_session, name='book_session'),
]

