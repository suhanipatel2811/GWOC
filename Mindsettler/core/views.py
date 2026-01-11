from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def base(request):
    return render(request, 'core/base.html')

def about(request):
    return render(request, 'core/about.html')

def psycho_education(request):
    # Track activity for logged-in users
    if request.user.is_authenticated:
        from users.models import Activity
        Activity.objects.create(
            user=request.user,
            action='Completed module: Psycho Education'
        )
    return render(request, 'core/pyscho_education.html')

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