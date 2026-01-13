from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from .models import Profile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    # Phone validator for international format
    phone_validator = RegexValidator(
        regex=r'^\+[1-9]\d{6,14}$',
        message="Phone number must be in international format (e.g., +911234567890)"
    )
    
    phone = forms.CharField(
        required=True, 
        max_length=15,
        validators=[phone_validator],
        help_text="Enter phone number with country code (e.g., +911234567890)"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "phone"]

    def clean_phone(self):
        """Validate that phone number is unique."""
        phone = self.cleaned_data.get('phone', '').strip()
        
        # Check if phone already exists
        if Profile.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "This phone number is already registered. Please use another number or login."
            )
        
        return phone

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
