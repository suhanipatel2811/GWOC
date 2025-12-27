from django import forms
from .models import Appointment, SessionSlot

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['full_name', 'email', 'phone', 'slot']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'slot': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only available slots
        self.fields['slot'].queryset = SessionSlot.objects.filter(is_available=True)


class RescheduleForm(forms.Form):
    slot = forms.ModelChoiceField(
        queryset=SessionSlot.objects.filter(is_available=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Choose a new date & time"
    )
