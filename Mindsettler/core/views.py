from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def base(request):
    return render(request, 'core/base.html')

def about(request):
    return render(request, 'core/about.html')

def psycho_education(request):
    return render(request, 'core/pyscho_education.html')

def how_it_works(request):
    return render(request, 'core/how_it_works.html')

def what(request):
    return render(request, 'core/what.html')

def journey(request):
    return render(request, 'core/journey.html')

def what_makes_us_different(request):
    return render(request, 'core/what_makes_us_different.html')