from django import forms
from .models import CorporateServiceRequest

class CorporateServiceRequestForm(forms.ModelForm):
    class Meta:
        model = CorporateServiceRequest
        fields = [
            'company_name',
            'contact_person',
            'email',
            'phone',
            'service_type',
            'number_of_employees',
            'preferred_date',
            'message'
        ]

        widgets = {
            'preferred_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'message': forms.Textarea(
                attrs={'rows': 4}
            )
        }
        labels = {
            'company_name': 'Company Name',
            'contact_person': 'Contact Person',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'service_type': 'Type of Service',
            'number_of_employees': 'Number of Employees',
            'preferred_date': 'Preferred Date',
            'message': 'Additional Information'
        }
