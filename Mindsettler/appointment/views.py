from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone
from django.http import HttpResponse
try:
    import stripe
except Exception:
    stripe = None

if stripe and hasattr(settings, 'STRIPE_SECRET_KEY'):
    stripe.api_key = settings.STRIPE_SECRET_KEY

from .models import Appointment, SessionSlot
from .forms import AppointmentForm, RescheduleForm
from urllib.parse import quote
import json
from django.contrib.auth.models import User
try:
    from google.oauth2.credentials import Credentials as GoogleCredentials
    from googleapiclient.discovery import build as google_build
except Exception:
    GoogleCredentials = None
    google_build = None

def booking(request):
    # Require login to book a session
    if not request.user.is_authenticated:
        messages.info(request, "Please login first")
        login_url = reverse('users:login')
        return redirect(f"{login_url}?next={request.path}")
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            slot = appointment.slot

            if not slot.is_available:
                messages.error(request, "This slot is already booked")
                return redirect('appointment:booking')

            # mark appointment pending confirmation
            appointment.status = 'PENDING'
            appointment.save()

            # lock the slot
            slot.is_available = False
            slot.save()

            # If the booking user has linked Google Calendar credentials, create the event server-side
            if request.user.is_authenticated and GoogleCredentials is not None:
                try:
                    cred_obj = getattr(request.user, 'google_credentials', None)
                    if cred_obj and cred_obj.credentials:
                        cred_data = json.loads(cred_obj.credentials)
                        creds = GoogleCredentials.from_authorized_user_info(cred_data, scopes=['https://www.googleapis.com/auth/calendar.events'])

                        service = google_build('calendar', 'v3', credentials=creds)
                        # prepare event body
                        try:
                            start_dt = timezone.make_aware(datetime.combine(slot.date, slot.time))
                        except Exception:
                            start_dt = datetime.combine(slot.date, slot.time)
                            start_dt = timezone.make_aware(start_dt)
                        end_dt = start_dt + timedelta(minutes=appointment.duration_minutes or 60)

                        event = {
                            'summary': f"MindSettler Session - {appointment.full_name}",
                            'description': appointment.location_details or 'MindSettler session',
                            'start': {'dateTime': start_dt.isoformat()},
                            'end': {'dateTime': end_dt.isoformat()},
                        }

                        # insert into primary calendar
                        try:
                            service.events().insert(calendarId='primary', body=event).execute()
                        except Exception:
                            # don't block booking on calendar errors
                            pass
                except Exception:
                    pass

            # If user requested Google Calendar add, generate a calendar link
            if appointment.add_to_google_calendar:
                try:
                    start_dt = timezone.make_aware(datetime.combine(slot.date, slot.time))
                except Exception:
                    start_dt = datetime.combine(slot.date, slot.time)
                    start_dt = timezone.make_aware(start_dt)

                end_dt = start_dt + timedelta(minutes=appointment.duration_minutes or 60)
                start_utc = start_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                end_utc = end_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')

                from urllib.parse import quote
                title = quote(f"MindSettler Session - {appointment.full_name}")
                details = quote('MindSettler consultation session')
                location = quote(appointment.location_details or 'MindSettler Online / Studio')


                # include the user's email as an attendee so the event is added to their calendar when they are signed in
                try:
                    attendee = quote(appointment.email)
                except Exception:
                    attendee = ''

                add_param = f"&add=mailto:{attendee}" if attendee else ''

                gcal_url = (
                    "https://www.google.com/calendar/render?action=TEMPLATE"
                    f"&text={title}&dates={start_utc}/{end_utc}&details={details}&location={location}{add_param}"
                )

                appointment.google_calendar_link = gcal_url
                appointment.save()

            # No payment gateway: show confirmation with manual payment instructions
            return redirect(reverse('appointment:confirmation') + f"?id={appointment.id}")

        else:
            print("Form errors:", form.errors)

    else:
        form = AppointmentForm()

    return render(request, "appointment/booking.html", {"form": form})

def payment_success(request, appointment_id):
    # kept for backward compatibility if stripe ever used
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.payment_confirmed = True
    appointment.status = 'CONFIRMED'
    appointment.save()
    return redirect("appointment:confirmation")

def payment_cancel(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'PENDING'
    appointment.payment_confirmed = False
    appointment.save()

    # Unlock slot
    slot = appointment.slot
    slot.is_available = True
    slot.save()

    return redirect("appointment:booking")

def confirmation(request):
    appt_id = request.GET.get('id')
    appointment = None
    if appt_id:
        appointment = get_object_or_404(Appointment, id=appt_id)
    else:
        appointment = Appointment.objects.filter(payment_confirmed=True).order_by("-booked_on").first()

    gcal_url = None
    ics_url = None
    if appointment:
        # build Google Calendar URL and ICS download url for the template
        try:
            start_dt = timezone.make_aware(datetime.combine(appointment.slot.date, appointment.slot.time))
        except Exception:
            start_dt = datetime.combine(appointment.slot.date, appointment.slot.time)
            start_dt = timezone.make_aware(start_dt)

        end_dt = start_dt + timedelta(minutes=appointment.duration_minutes or 60)
        start_utc = start_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        end_utc = end_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')

        title = quote(f"MindSettler Session - {appointment.full_name}")
        details = quote('MindSettler consultation session')
        location = quote(appointment.location_details or 'MindSettler Online / Studio')

        try:
            attendee = quote(appointment.email)
        except Exception:
            attendee = ''

        add_param = f"&add=mailto:{attendee}" if attendee else ''

        if appointment.google_calendar_link:
            gcal_url = appointment.google_calendar_link
        else:
            gcal_url = (
                "https://www.google.com/calendar/render?action=TEMPLATE"
                f"&text={title}&dates={start_utc}/{end_utc}&details={details}&location={location}{add_param}"
            )

        ics_url = reverse('appointment:download_ics', args=[appointment.id])

    return render(request, "appointment/confirmation.html", {"appointment": appointment, "gcal_url": gcal_url, "ics_url": ics_url})


def download_ics(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    try:
        start_dt = timezone.make_aware(datetime.combine(appointment.slot.date, appointment.slot.time))
    except Exception:
        start_dt = datetime.combine(appointment.slot.date, appointment.slot.time)
        start_dt = timezone.make_aware(start_dt)

    end_dt = start_dt + timedelta(minutes=appointment.duration_minutes or 60)

    dtstamp = timezone.now().astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    start_utc = start_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    end_utc = end_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    uid = f"{appointment.id}@mindsettler"
    summary = f"MindSettler Session - {appointment.full_name}"
    description = appointment.location_details or 'MindSettler session'
    location = appointment.location_details or 'MindSettler Online / Studio'

    ics = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//MindSettler//EN\n"
        "BEGIN:VEVENT\n"
        f"UID:{uid}\n"
        f"DTSTAMP:{dtstamp}\n"
        f"DTSTART:{start_utc}\n"
        f"DTEND:{end_utc}\n"
        f"SUMMARY:{summary}\n"
        f"DESCRIPTION:{description}\n"
        f"LOCATION:{location}\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )

    filename = f"mindsettler_session_{appointment.id}.ics"
    response = HttpResponse(ics, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def appointment_status(request):
    # If the user is staff show all appointments; otherwise show only appointments for the logged-in user's email
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            appointments = Appointment.objects.all().order_by('-booked_on')
        else:
            user_email = getattr(request.user, 'email', None)
            if user_email:
                appointments = Appointment.objects.filter(email=user_email).order_by('-booked_on')
            else:
                appointments = Appointment.objects.none()
    else:
        # Require login to view appointments
        messages.info(request, "Please login to view your appointments.")
        login_url = reverse('users:login')
        return redirect(f"{login_url}?next={request.path}")

    return render(request, 'appointment/appointment_status.html', {'appointments': appointments})

def my_appointments(request):
    appointments = Appointment.objects.select_related('slot').filter(email=request.user.email) if request.user.is_authenticated else Appointment.objects.none()
    return render(request, 'core/about.html', {
        'appointments': appointments
    })
    
    

def cancel_appointment(request, appointment_id):
    # Show the confirmation page
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, 'appointment/cancel_appointment.html', {'appointment': appointment})

def confirm_cancellation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        # Get bank details from POST
        account_name = request.POST.get('account_name')
        account_number = request.POST.get('account_number')
        ifsc = request.POST.get('ifsc')

        # Here you can call your payment/refund logic
        # Example: refund_user(account_name, account_number, ifsc, amount)

        # Mark appointment as cancelled
        appointment.status = 'CANCELLED'
        appointment.save()

        # Use slot date/time for the message and unlock the slot
        slot = getattr(appointment, 'slot', None)
        if slot:
            slot.is_available = True
            slot.save()

            time_str = slot.time.strftime('%I:%M %p') if hasattr(slot.time, 'strftime') else slot.time
            date_str = slot.date
            messages.success(request, f"Your appointment on {date_str} at {time_str} has been successfully cancelled and refund is processed.")
        else:
            messages.success(request, "Your appointment has been successfully cancelled and refund is processed.")

        return redirect('appointment:status')  # Go back to appointments list

    return render(request, 'appointment/confirm_cancellation.html', {'appointment': appointment})

def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        form = RescheduleForm(request.POST)
        if form.is_valid():
            new_slot = form.cleaned_data['slot']

            # ensure selected slot is still available
            if not new_slot.is_available:
                messages.error(request, "Selected slot is no longer available. Please choose another.")
                return redirect('appointment:reschedule_appointment', appointment_id=appointment.id)

            # unlock previous slot
            old_slot = getattr(appointment, 'slot', None)
            if old_slot:
                old_slot.is_available = True
                old_slot.save()

            # assign new slot and lock it
            appointment.slot = new_slot
            appointment.save()

            new_slot.is_available = False
            new_slot.save()

            time_str = new_slot.time.strftime('%I:%M %p') if hasattr(new_slot.time, 'strftime') else new_slot.time
            messages.success(request, f"Appointment rescheduled to {new_slot.date} at {time_str}.")
            return redirect('appointment:status')
    else:
        form = RescheduleForm()

    return render(
        request,
        'appointment/reschedule_appointment.html',
        {'appointment': appointment, 'form': form}
    )
