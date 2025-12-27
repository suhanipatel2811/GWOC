from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CorporateServiceRequestForm
from django.core.mail import send_mail
from django.conf import settings

def corporate_services(request):
    return render(request, 'corporate/corporate_services.html')

def request_service(request):
    if request.method == 'POST':
        form = CorporateServiceRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save()
            subject = "New Corporate Service Request"
            message = (
                f"Company Name: {request_obj.company_name}\n"
                f"Contact Person: {request_obj.contact_person}\n"
                f"Email: {request_obj.email}\n"
                f"Phone: {request_obj.phone}\n\n"
                f"Service Type: {request_obj.service_type}\n"
                f"Employees: {request_obj.number_of_employees}\n"
                f"Preferred Date: {request_obj.preferred_date}\n\n"
                f"Message:\n{request_obj.message}\n"
            )

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['mindsettler@gmail.com'],
                fail_silently=False,
            )

            messages.success(request, "Your request has been submitted successfully!")
            return redirect('corporate:corporate_services')
    else:
        form = CorporateServiceRequestForm()

    return render(request, 'corporate/request_service.html', {'form': form})