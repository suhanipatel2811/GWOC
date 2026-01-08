from django.urls import path
from .views import register_view, login_view, logout_view, profile_view, update_profile, upload_avatar, change_password
from .views import google_connect, google_callback, google_disconnect

app_name = 'users' 
urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("profile/update/", update_profile, name="update_profile"),
    path("profile/avatar/", upload_avatar, name="upload_avatar"),
    path("profile/change-password/", change_password, name="change_password"),
    path("profile/google/connect/", google_connect, name="google_connect"),
    path("profile/google/callback/", google_callback, name="google_callback"),
    path("profile/google/disconnect/", google_disconnect, name="google_disconnect"),
]
