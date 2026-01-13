from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone, date as date_class
from django.db import transaction
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
        # Keep existing form handling when client posts a slot id
        if 'slot' in request.POST:
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
            else:
                print("Form errors:", form.errors)
        else:
            # Support AJAX/simple POSTs that supply date & time strings instead of a slot id
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            session_type = request.POST.get('session_type', 'ONLINE')

            if not date_str or not time_str:
                return HttpResponse('Missing date or time', status=400)

            try:
                slot_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except Exception:
                return HttpResponse('Invalid date format', status=400)

            try:
                # expect times like '09:00 AM'
                slot_time = datetime.strptime(time_str, '%I:%M %p').time()
            except Exception:
                # fallback to 24h like '09:00'
                try:
                    slot_time = datetime.strptime(time_str, '%H:%M').time()
                except Exception:
                    return HttpResponse('Invalid time format', status=400)

            # don't allow booking past dates
            if slot_date < date_class.today():
                return HttpResponse('Cannot book past dates', status=400)

            # create or obtain the slot and atomically check availability
            try:
                with transaction.atomic():
                    slot, created = SessionSlot.objects.select_for_update().get_or_create(date=slot_date, time=slot_time, defaults={'is_available': True})
                    if not slot.is_available:
                        return HttpResponse('Selected slot is no longer available', status=400)

                    # create appointment with minimal required fields
                    # attempt to fill from logged-in user where possible
                    full_name = request.POST.get('full_name') or getattr(request.user, 'get_full_name', lambda: '')() or request.user.username
                    email = request.POST.get('email') or getattr(request.user, 'email', '')
                    phone = request.POST.get('phone') or ''

                    appointment = Appointment.objects.create(
                        full_name=full_name,
                        email=email,
                        phone=phone,
                        slot=slot,
                        session_type=(session_type.upper() if session_type else 'ONLINE')
                    )

                    # lock the slot
                    slot.is_available = False
                    slot.save()

            except Exception as e:
                return HttpResponse('Booking failed', status=500)

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

            # Redirect to payment page
            return redirect(reverse('appointment:payment', kwargs={'appointment_id': appointment.id}))


    else:
        form = AppointmentForm()

    today_iso = date_class.today().isoformat()
    return render(request, "appointment/booking.html", {"form": form, 'today': today_iso})


def available_slots(request):
    """Return JSON availability for standard hourly slots for a given date.

    Query param: ?date=YYYY-MM-DD
    Response: {"09:00 AM": true, "10:00 AM": false, ...}
    """
    from django.http import JsonResponse

    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'date required'}, status=400)

    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return JsonResponse({'error': 'invalid date'}, status=400)

    # Do not expose past dates
    if query_date < date_class.today():
        return JsonResponse({'error': 'date in past'}, status=400)

    availability = {}
    def fmt(h):
        ampm = 'AM' if h < 12 else 'PM'
        h12 = ((h + 11) % 12) + 1
        return f"{str(h12).zfill(2)}:00 {ampm}"

    for h in range(9, 18):
        time_obj = datetime.strptime(f"{str(h).zfill(2)}:00", '%H:%M').time()
        # if there's a slot and it's not available, mark false
        slot_qs = SessionSlot.objects.filter(date=query_date, time=time_obj)
        if slot_qs.exists():
            availability[fmt(h)] = slot_qs.filter(is_available=True).exists()
        else:
            # slot not created yet -> available
            availability[fmt(h)] = True

    return JsonResponse(availability)

def payment_success(request, appointment_id):
    # kept for backward compatibility if stripe ever used
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.payment_confirmed = True
    appointment.status = 'CONFIRMED'
    appointment.save()
    
    # Track activity
    from users.models import Activity
    Activity.objects.create(
        user=appointment.user,
        action=f'Booked session: {appointment.session_type} on {appointment.slot.start_time.strftime("%B %d, %Y")}'
    )
    
    return redirect(reverse('appointment:payment', kwargs={'appointment_id': appointment.id}))

def payment(request, appointment_id):
    """Display payment page for the appointment."""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    return render(request, "appointment/payment.html", {"appointment": appointment})

def confirm_payment(request, appointment_id):
    """Confirm payment and mark appointment as confirmed."""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'CONFIRMED'
    appointment.payment_confirmed = True
    appointment.payment_mode = 'UPI'
    appointment.save()
    
    # Log activity
    if request.user.is_authenticated:
        Activity.objects.create(
            user=request.user,
            action=f'Payment completed for session on {appointment.slot.date.strftime("%B %d, %Y")}'
        )
    
    return redirect(f"{reverse('appointment:confirmation')}?id={appointment.id}")

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
