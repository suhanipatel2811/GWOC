from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def home(request):
    # If user is authenticated, log them out when they visit home page
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'home.html')

def base(request):
    return render(request, 'core/base.html')

@login_required
def about(request):
    return render(request, 'core/about.html')

@login_required
def psycho_education(request):
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action='Completed module: Psycho Education'
        )
    return render(request, 'core/pyscho_education.html')

@login_required
def how_it_works(request):
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action='Completed module: How It Works'
        )
    return render(request, 'core/how_it_works.html')

def what(request):
    return render(request, 'core/what.html')

@login_required
def journey(request):
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action='Completed module: Your Journey'
        )
    return render(request, 'core/journey.html')

def what_makes_us_different(request):
    return render(request, 'core/what_makes_us_different.html')
def book_session(request):
    return render(request, 'core/book_session.html')

def privacypolicy(request):
    return render(request, 'core/privacypolicy.html')

def usa(request):
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action='Read article: Understanding Anxiety Triggers'
        )
    return render(request, 'core/usa.html')

def morning_grounding(request):
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action='Completed practice: Morning Grounding'
        )
    return render(request, 'core/morning_grounding.html')

def gratitude_journaling(request):
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action='Completed practice: Gratitude Journaling'
        )
    return render(request, 'core/gratitude_journaling.html')