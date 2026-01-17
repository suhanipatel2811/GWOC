from django.shortcuts import  redirect, render
from django.contrib import messages
from .forms import ContactForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from django.conf import settings
from .models import ChatMessage

# Only import OpenAI if the API key is configured
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(settings.OPENAI_API_KEY)
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

@login_required
def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact:contact')  # or success page
            
        else:
            print(form.errors)
    else:
        form = ContactForm()

    return render(request, 'contact/contact.html', {'form': form})


@login_required
def chatbot_view(request):
    return render(request, 'contact/chatbot.html')


@login_required
def chatbot_api(request):
    print("🔥 chatbot_api CALLED")

    if request.method == "POST":
        # Check if OpenAI is available and configured
        if not OPENAI_AVAILABLE or not settings.OPENAI_API_KEY:
            return JsonResponse({
                "error": "AI chatbot is not configured. Please add OPENAI_API_KEY to enable this feature."
            }, status=503)

        print("🔥 POST request received")
        print("API KEY:", settings.OPENAI_API_KEY[:20] + "..." if settings.OPENAI_API_KEY else "NOT SET")

        user_message = request.POST.get("message")
        print("User message:", user_message)

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            reply = response.choices[0].message.content
            print("AI reply:", reply)

            return JsonResponse({"reply": reply})
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return JsonResponse({
                "error": "Failed to get response from AI. Please try again later."
            }, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
