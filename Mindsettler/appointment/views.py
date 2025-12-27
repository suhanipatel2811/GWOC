from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
try:
    import stripe
except Exception:
    stripe = None

if stripe:
    stripe.api_key = settings.STRIPE_SECRET_KEY

from .models import Appointment, SessionSlot
from .forms import AppointmentForm, RescheduleForm

def booking(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            slot = appointment.slot

            if not slot.is_available:
                messages.error(request, "This slot is already booked")
                return redirect('appointment:booking')

            
            appointment.payment_status = "PENDING"
            appointment.save()

            if not stripe:
                messages.error(request, "Payment service unavailable. Please try again later.")
                appointment.payment_status = "FAILED"
                appointment.save()
                slot.is_available = True
                slot.save()
                return redirect('appointment:booking')

            # Create Stripe session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "inr",
                        "product_data": {"name": f"Session on {slot.date} at {slot.time}"},
                        "unit_amount": 50000,  # ₹500
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=request.build_absolute_uri(f"/appointment/payment-success/{appointment.id}/"),
                cancel_url=request.build_absolute_uri(f"/appointment/payment-cancel/{appointment.id}/"),
            )

            appointment.stripe_session_id = session.id
            appointment.save()
            
            # Lock the slot
            slot.is_available = False
            slot.save()


            return redirect(session.url)

        else:
            print("Form errors:", form.errors)

    else:
        form = AppointmentForm()

    return render(request, "appointment/booking.html", {"form": form})

def payment_success(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.payment_status = "PAID"
    appointment.save()
    return redirect("appointment:confirmation")

def payment_cancel(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.payment_status = "FAILED"
    appointment.save()

    # Unlock slot
    slot = appointment.slot
    slot.is_available = True
    slot.save()

    return redirect("appointment:booking")

def confirmation(request):
    appointment = Appointment.objects.filter(payment_status="PAID").order_by("-booked_on").first()
    return render(request, "appointment/confirmation.html", {"appointment": appointment})

def appointment_status(request):
    appointments = Appointment.objects.all().order_by('-booked_on')
    return render(request, 'appointment/appointment_status.html', {'appointments': appointments})

def my_appointments(request):
    print("🔥 MY_APPOINTMENTS VIEW HIT 🔥")
    appointments = Appointment.objects.select_related('slot')

    now = timezone.localtime()

    for appointment in appointments:
        slot_datetime = datetime.combine(
            appointment.slot.date,
            appointment.slot.time
        )
        slot_datetime = timezone.make_aware(slot_datetime)

        if slot_datetime < now:
            appointment.status = "Done"
        else:
            appointment.status = "Pending"

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
        appointment.status = 'Cancelled'
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
