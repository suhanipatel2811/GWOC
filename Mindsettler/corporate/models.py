from django.db import models

class CorporateServiceRequest(models.Model):
    SERVICE_CHOICES = [
        ('workshop', 'Mental Health Workshop'),
        ('training', 'Employee Training Program'),
        ('consulting', 'Organizational Consulting'),
        ('wellbeing', 'Well-being Session'),
    ]

    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)

    service_type = models.CharField(
        max_length=50,
        choices=SERVICE_CHOICES
    )

    number_of_employees = models.PositiveIntegerField()
    preferred_date = models.DateField()
    message = models.TextField(help_text="Describe your requirements")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.service_type}"
    class Meta:
        verbose_name = "Corporate Service Request"
        verbose_name_plural = "Corporate Service Requests"