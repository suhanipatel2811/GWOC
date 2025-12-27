from django.shortcuts import  redirect, render
from django.contrib import messages
from .forms import ContactForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from openai import OpenAI
from .models import ChatMessage
client = OpenAI(api_key=settings.OPENAI_API_KEY)

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


def chatbot_view(request):
    return render(request, 'contact/chatbot.html')


def chatbot_api(request):
    print("🔥 chatbot_api CALLED")

    if request.method == "POST":
        print("🔥 POST request received")
        print("API KEY:", settings.OPENAI_API_KEY)

        user_message = request.POST.get("message")
        print("User message:", user_message)

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

    return JsonResponse({"error": "Invalid request"})
