from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True, max_length=15)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "phone"]

    def save(self, commit=True):
        # Save the User first
        user = super().save(commit=commit)
        # Ensure Profile exists (post_save should normally create it)
        phone = self.cleaned_data.get('phone', '')
        try:
            profile = user.profile
            profile.phone = phone
            profile.save()
        except Exception:
            # If for some reason profile isn't present, create one
            Profile.objects.create(user=user, phone=phone)
        return user
