from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from .models import Activity
from django.conf import settings
from django.urls import reverse
from django.shortcuts import get_object_or_404
from .models import GoogleCalendarCredential

# Google OAuth libraries are optional; guard imports
try:
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except Exception:
    Flow = None
    Credentials = None
    build = None

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # honor `next` parameter if present, else go to about page
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:about')
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            # honor `next` parameter if present, else go to about page
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:about')
    else:
        form = AuthenticationForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('core:home')


@login_required
def profile_view(request):
    activities = Activity.objects.filter(user=request.user).order_by('-timestamp')[:10]
    return render(request, "users/profile.html", {"activities": activities})


@login_required
@require_POST
def update_profile(request):
    """Accepts POST to update `first_name`, `last_name`, and `email` for the logged-in user.
    Returns JSON success or error message.
    """
    first = request.POST.get('first_name', '').strip()
    last = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()

    if email and '@' not in email:
        return JsonResponse({'success': False, 'error': 'Enter a valid email address.'}, status=400)

    user = request.user
    user.first_name = first
    user.last_name = last
    if email:
        user.email = email
    user.save()

    return JsonResponse({'success': True, 'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email})


@login_required
@require_POST
def upload_avatar(request):
    if 'avatar' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded.'}, status=400)

    avatar = request.FILES['avatar']
    profile = request.user.profile
    profile.avatar = avatar
    profile.save()

    url = profile.avatar.url if profile.avatar else ''
    Activity.objects.create(user=request.user, action='avatar_updated')
    return JsonResponse({'success': True, 'avatar_url': url})


@login_required
@require_POST
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        Activity.objects.create(user=request.user, action='password_changed')
        return JsonResponse({'success': True})
    else:
        # return first error
        errors = form.errors.as_json()
        return JsonResponse({'success': False, 'errors': errors}, status=400)


@login_required
def google_connect(request):
    if Flow is None:
        return redirect('users:profile')

    client_config = {
        "web": {
            "client_id": getattr(settings, 'GOOGLE_CLIENT_ID', ''),
            "client_secret": getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    redirect_uri = request.build_absolute_uri(reverse('users:google_callback'))
    scopes = ['https://www.googleapis.com/auth/calendar.events', 'openid', 'email', 'profile']

    flow = Flow.from_client_config(client_config=client_config, scopes=scopes, redirect_uri=redirect_uri)
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    request.session['google_oauth_state'] = state
    return redirect(auth_url)


@login_required
def google_callback(request):
    if Flow is None:
        return redirect('users:profile')

    state = request.session.pop('google_oauth_state', None)
    client_config = {
        "web": {
            "client_id": getattr(settings, 'GOOGLE_CLIENT_ID', ''),
            "client_secret": getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    redirect_uri = request.build_absolute_uri(reverse('users:google_callback'))

    flow = Flow.from_client_config(client_config=client_config, scopes=['https://www.googleapis.com/auth/calendar.events'], state=state, redirect_uri=redirect_uri)
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials

    # persist credentials
    cred_obj, _ = GoogleCalendarCredential.objects.get_or_create(user=request.user)
    try:
        cred_obj.credentials = creds.to_json()
    except Exception:
        cred_obj.credentials = ''
    try:
        cred_obj.expires_at = creds.expiry
    except Exception:
        cred_obj.expires_at = None
    cred_obj.save()

    return redirect('users:profile')


@login_required
def google_disconnect(request):
    obj = getattr(request.user, 'google_credentials', None)
    if obj:
        obj.credentials = ''
        obj.expires_at = None
        obj.save()
    return redirect('users:profile')
