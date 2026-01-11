from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from .models import Activity, Profile, MoodEntry
from django.contrib.auth.models import User
from django.contrib import messages
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
        phone = request.POST.get('phone', '').strip()
        # If phone already registered, show error and redirect back to register
        if phone and Profile.objects.filter(phone=phone).exists():
            messages.error(request, 'This Phone no is already registered. Please try another phone number')
            return redirect('users:register')

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registered successfully')
            # Send newly-registered users to profile image selection page
            return redirect('users:profileimage')
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            # honor `next` parameter if present, else go to profile image page
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('users:profileimage')
        else:
            # Allow login using phone number or email: if the form failed, try authenticating
            # by looking up the user with the provided email or Profile.phone and authenticating
            username_or_phone = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            found = False
            if username_or_phone and password:
                # try find user by email first
                # there may be multiple users with the same email; try each one
                users_with_email = User.objects.filter(email=username_or_phone)
                for user_obj in users_with_email:
                    user = authenticate(request, username=user_obj.username, password=password)
                    if user:
                        login(request, user)
                        return redirect('users:profileimage')

                # try find profile by phone
                try:
                    profile = Profile.objects.get(phone=username_or_phone)
                    user = authenticate(request, username=profile.user.username, password=password)
                    if user:
                        login(request, user)
                        return redirect('users:profileimage')
                except Profile.DoesNotExist:
                    pass

            # If we reach here, no user was found/authenticated
            messages.error(request, 'Please create account first then try again')
    else:
        form = AuthenticationForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('core:home')


@login_required
def profile_view(request):
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q
    
    # Filter activities for Recent Journey - only show meaningful session/therapy activities
    activities = Activity.objects.filter(user=request.user).exclude(
        Q(action__icontains='login') | 
        Q(action__icontains='avatar') | 
        Q(action__icontains='profile_updated') |
        Q(action__icontains='password')
    ).order_by('-timestamp')[:10]
    
    # Calculate Days Mindful (unique days with activity)
    activity_dates = Activity.objects.filter(user=request.user).dates('timestamp', 'day')
    days_mindful = activity_dates.count()
    
    # Calculate Modules Completed (count activities with 'module' or 'completed' in action)
    modules_completed = Activity.objects.filter(
        user=request.user,
        action__icontains='module'
    ).count()
    
    # Calculate Current Streak (consecutive days with activity)
    current_streak = 0
    if activity_dates:
        today = timezone.now().date()
        current_date = today
        
        # Convert queryset to list of dates
        dates_list = list(activity_dates)
        
        # Check if user was active today or yesterday
        if dates_list and (dates_list[0] == today or dates_list[0] == today - timedelta(days=1)):
            for date in dates_list:
                if date == current_date or date == current_date - timedelta(days=1):
                    current_streak += 1
                    current_date = date - timedelta(days=1)
                else:
                    break
    
    # Get today and yesterday for template
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get mood data for the graph (default to 7 days)
    days_param = int(request.GET.get('days', 7))  # 7 or 30 days
    from .models import MoodEntry
    mood_entries = MoodEntry.objects.filter(
        user=request.user,
        date__gte=today - timedelta(days=days_param-1)
    ).order_by('date')
    
    # Prepare mood data for the graph
    mood_data = []
    mood_labels = []
    for i in range(days_param):
        date = today - timedelta(days=days_param-1-i)
        mood = mood_entries.filter(date=date).first()
        mood_data.append(mood.mood_score if mood else 5)  # Default to 5 if no entry
        if days_param == 7:
            mood_labels.append(date.strftime('%a'))  # Mon, Tue, etc.
        else:
            mood_labels.append(date.strftime('%b %d'))  # Jan 01, etc.
    
    import json
    context = {
        'activities': activities,
        'days_mindful': days_mindful,
        'modules_completed': modules_completed,
        'current_streak': current_streak,
        'today': today,
        'yesterday': yesterday,
        'mood_data': json.dumps(mood_data),
        'mood_labels': json.dumps(mood_labels),
        'days_param': days_param,
    }
    
    return render(request, "users/profile.html", context)


@login_required
def profileimage_view(request):
    """Display avatar selection page and save choice."""
    if request.method == "POST":
        avatar_choice = request.POST.get('avatar_choice', '')
        
        # Save the avatar choice to the user's profile
        if avatar_choice:
            profile = request.user.profile
            profile.avatar_type = avatar_choice
            profile.save()
            
            # Log the activity
            Activity.objects.create(
                user=request.user,
                action=f'Selected {avatar_choice} avatar'
            )
            
            messages.success(request, f'Avatar updated successfully!')
            
        return redirect('users:profile')
    return render(request, "users/profileimage.html")


@login_required
def overview_view(request):
    """Display user overview/dashboard page."""
    from django.utils import timezone
    from datetime import timedelta
    from appointment.models import Appointment
    from resources.models import Article
    from .models import MoodEntry
    from django.db.models import Avg, Q
    
    activities = Activity.objects.filter(user=request.user).order_by('-timestamp')[:10]
    today = timezone.now().date()
    
    # Calculate Days Mindful
    activity_dates = Activity.objects.filter(user=request.user).dates('timestamp', 'day')
    days_mindful = activity_dates.count()
    
    # Calculate Modules Completed
    modules_completed = Activity.objects.filter(
        user=request.user,
        action__icontains='module'
    ).count()
    
    # Calculate Current Streak
    current_streak = 0
    if activity_dates:
        current_date = today
        dates_list = list(activity_dates)
        
        if dates_list and (dates_list[0] == today or dates_list[0] == today - timedelta(days=1)):
            for date in dates_list:
                if date == current_date or date == current_date - timedelta(days=1):
                    current_streak += 1
                    current_date = date - timedelta(days=1)
                else:
                    break
    
    # Get upcoming appointments for this user (by email)
    upcoming_appointments = Appointment.objects.filter(
        email=request.user.email,
        slot__date__gte=today,
        status__in=['PENDING', 'CONFIRMED']
    ).select_related('slot').order_by('slot__date', 'slot__time')[:5]
    
    # Count appointments this week
    week_end = today + timedelta(days=7)
    appointments_this_week = Appointment.objects.filter(
        email=request.user.email,
        slot__date__gte=today,
        slot__date__lte=week_end,
        status__in=['PENDING', 'CONFIRMED']
    ).count()
    
    # Get next appointment
    next_appointment = upcoming_appointments.first()
    
    # Get recommended articles (latest 5)
    recommended_articles = Article.objects.all().order_by('-created_at')[:5]
    articles_count = recommended_articles.count()
    
    # Calculate mood summary (last 7 days)
    week_ago = today - timedelta(days=7)
    mood_entries = MoodEntry.objects.filter(
        user=request.user,
        date__gte=week_ago
    )
    
    avg_mood = mood_entries.aggregate(Avg('mood_score'))['mood_score__avg'] or 5
    
    # Determine mood status
    if avg_mood >= 8:
        mood_status = "Very Happy"
        mood_percentage = 90
    elif avg_mood >= 7:
        mood_status = "Generally Calm"
        mood_percentage = 70
    elif avg_mood >= 5:
        mood_status = "Balanced"
        mood_percentage = 50
    elif avg_mood >= 3:
        mood_status = "Slightly Low"
        mood_percentage = 35
    else:
        mood_status = "Need Support"
        mood_percentage = 20
    
    # Prepare mood data for weekly graph (last 7 days)
    import json
    mood_data_week = []
    mood_labels_week = []
    for i in range(7):
        date = today - timedelta(days=6-i)
        mood = mood_entries.filter(date=date).first()
        mood_data_week.append(mood.mood_score if mood else 5)
        mood_labels_week.append(date.strftime('%a'))
    
    # Get member since date
    member_since = request.user.date_joined.year
    
    context = {
        'activities': activities,
        'days_mindful': days_mindful,
        'modules_completed': modules_completed,
        'current_streak': current_streak,
        'upcoming_appointments': upcoming_appointments,
        'appointments_this_week': appointments_this_week,
        'next_appointment': next_appointment,
        'recommended_articles': recommended_articles,
        'articles_count': articles_count,
        'mood_status': mood_status,
        'mood_percentage': mood_percentage,
        'avg_mood': round(avg_mood, 1),
        'member_since': member_since,
        'today': today,
        'mood_data_week': json.dumps(mood_data_week),
        'mood_labels_week': json.dumps(mood_labels_week),
    }
    
    return render(request, "users/overview.html", context)


@login_required
def myprogress_view(request):
    """Display user progress tracking page."""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Avg, Count
    from appointment.models import Appointment
    
    today = timezone.now().date()
    
    # Get user activities
    activities = Activity.objects.filter(user=request.user).order_by('-timestamp')[:10]
    
    # Calculate Days Mindful
    activity_dates = Activity.objects.filter(user=request.user).dates('timestamp', 'day')
    days_mindful = activity_dates.count()
    
    # Calculate Modules Completed
    modules_completed = Activity.objects.filter(
        user=request.user,
        action__icontains='module'
    ).count()
    
    # Calculate Current Streak
    current_streak = 0
    if activity_dates:
        current_date = today
        dates_list = list(activity_dates)
        
        if dates_list and (dates_list[0] == today or dates_list[0] == today - timedelta(days=1)):
            for date in dates_list:
                if date == current_date or date == current_date - timedelta(days=1):
                    current_streak += 1
                    current_date = date - timedelta(days=1)
                else:
                    break
    
    # Get mood data for last 30 days
    thirty_days_ago = today - timedelta(days=30)
    mood_entries = MoodEntry.objects.filter(
        user=request.user,
        date__gte=thirty_days_ago
    ).order_by('date')
    
    mood_data = [entry.mood_score for entry in mood_entries]
    mood_labels = [entry.date.strftime('%b %d') for entry in mood_entries]
    
    # Get session/activity counts for last 5 weeks
    activity_weeks = []
    max_count = 1  # Track max for scaling
    for i in range(4, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7*i)
        week_end = week_start + timedelta(days=6)
        week_activities = Activity.objects.filter(
            user=request.user,
            timestamp__date__gte=week_start,
            timestamp__date__lte=week_end
        ).count()
        if week_activities > max_count:
            max_count = week_activities
        activity_weeks.append({
            'count': week_activities,
            'label': week_start.strftime('%b %d')
        })
    
    # Calculate height percentages for each week
    for week in activity_weeks:
        if max_count > 0:
            week['height_percent'] = min(100, int((week['count'] / max_count) * 100))
        else:
            week['height_percent'] = 10 if week['count'] == 0 else 50
    
    # Calculate completed sessions
    completed_sessions = Appointment.objects.filter(
        email=request.user.email,
        status='CONFIRMED',
        slot__date__lt=today
    ).count()
    
    # Determine progress level
    if completed_sessions >= 20:
        level = "Emotional Master"
    elif completed_sessions >= 10:
        level = "Mindful Expert"
    elif completed_sessions >= 5:
        level = "Emotional Explorer"
    else:
        level = "Wellness Beginner"
    
    # Get member since year
    member_since = request.user.date_joined.year
    
    context = {
        'activities': activities,
        'days_mindful': days_mindful,
        'modules_completed': modules_completed,
        'current_streak': current_streak,
        'mood_data': mood_data,
        'mood_labels': mood_labels,
        'activity_weeks': activity_weeks,
        'completed_sessions': completed_sessions,
        'level': level,
        'member_since': member_since,
    }
    
    return render(request, "users/myprogress.html", context)


@login_required
def sessionhistory_view(request):
    """Display user session history page."""
    from django.utils import timezone
    from datetime import timedelta, datetime
    from appointment.models import Appointment
    from django.db.models import Sum, Q
    
    now = timezone.now()
    today = now.date()
    
    # Get user's full name for matching
    user_full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not user_full_name:
        user_full_name = request.user.username
    
    # Get all appointments for this user (by email AND name match)
    all_appointments = Appointment.objects.filter(
        email=request.user.email
    ).select_related('slot').order_by('-slot__date', '-slot__time')
    
    # Filter to only show appointments where full_name contains user's first name
    if request.user.first_name:
        all_appointments = all_appointments.filter(
            full_name__icontains=request.user.first_name
        )
    
    # Calculate total completed sessions and hours (past date+time AND confirmed)
    completed_appointments = all_appointments.filter(
        Q(status='CONFIRMED') & 
        (Q(slot__date__lt=today) | 
         Q(slot__date=today, slot__time__lt=now.time()))
    )
    total_completed = completed_appointments.count()
    total_hours = completed_appointments.aggregate(
        total=Sum('duration_minutes')
    )['total'] or 0
    total_hours = round(total_hours / 60, 1)  # Convert to hours
    
    # Get next scheduled appointment (future date+time)
    next_appointment = all_appointments.filter(
        Q(slot__date__gt=today) |
        Q(slot__date=today, slot__time__gte=now.time()),
        status__in=['PENDING', 'CONFIRMED']
    ).first()
    
    # Get member since year
    member_since = request.user.date_joined.year
    
    context = {
        'appointments': all_appointments[:20],  # Show last 20 appointments
        'total_completed': total_completed,
        'total_hours': total_hours,
        'next_appointment': next_appointment,
        'member_since': member_since,
        'today': today,
        'now': now,
    }
    
    return render(request, "users/sessionhistory.html", context)


@login_required
@require_POST
def update_preferences(request):
    """Update user preferences (email notifications, daily reminder, public profile)."""
    profile = request.user.profile
    profile.email_notifications = request.POST.get('email_notifications') == 'true'
    profile.daily_reminder = request.POST.get('daily_reminder') == 'true'
    profile.public_profile = request.POST.get('public_profile') == 'true'
    profile.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def update_profile(request):
    """Accepts POST to update `first_name`, `last_name`, `email`, and `phone` for the logged-in user."""
    first = request.POST.get('first_name', '').strip()
    last = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()

    if email and '@' not in email:
        messages.error(request, 'Enter a valid email address.')
        return redirect('users:profile')

    user = request.user
    user.first_name = first
    user.last_name = last
    if email:
        user.email = email
    user.save()
    
    # Update phone in profile
    if phone:
        profile = user.profile
        # Check if phone is already taken by another user
        existing = Profile.objects.filter(phone=phone).exclude(user=user).first()
        if existing:
            messages.error(request, 'This phone number is already registered to another account.')
            return redirect('users:profile')
        profile.phone = phone
        profile.save()
    
    messages.success(request, 'Profile updated successfully!')
    Activity.objects.create(user=request.user, action='profile_updated')
    return redirect('users:profile')


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


@login_required
def settings_view(request):
    """Display user settings page."""
    member_since = request.user.date_joined.year
    
    context = {
        'member_since': member_since,
    }
    
    return render(request, "users/settings.html", context)

