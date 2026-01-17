"""
Utility functions for appointment booking and calendar integration.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from urllib.parse import quote

logger = logging.getLogger('appointment')


def generate_google_calendar_link(appointment):
    """
    Generate a Google Calendar event link for an appointment.
    
    Args:
        appointment: Appointment model instance
        
    Returns:
        str: Google Calendar add event URL
    """
    try:
        from datetime import datetime, timezone as dt_timezone
        
        # Create timezone-aware datetime
        try:
            start_dt = timezone.make_aware(datetime.combine(appointment.slot.date, appointment.slot.time))
        except Exception:
            start_dt = datetime.combine(appointment.slot.date, appointment.slot.time)
            start_dt = timezone.make_aware(start_dt)
        
        end_dt = start_dt + timedelta(minutes=appointment.duration_minutes or 60)
        start_utc = start_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        end_utc = end_dt.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        
        # Encode parameters
        title = quote(f"MindSettler Session - {appointment.full_name}")
        details = quote('MindSettler consultation session')
        location = quote(appointment.location_details or 'MindSettler Online / Studio')
        
        # Include the user's email as an attendee
        attendee_param = ''
        if appointment.email:
            try:
                attendee = quote(appointment.email)
                attendee_param = f"&add=mailto:{attendee}"
            except Exception:
                pass
        
        gcal_url = (
            "https://www.google.com/calendar/render?action=TEMPLATE"
            f"&text={title}&dates={start_utc}/{end_utc}&details={details}&location={location}{attendee_param}"
        )
        
        return gcal_url
        
    except Exception as e:
        logger.error(f"Error generating Google Calendar link for appointment {appointment.id}: {str(e)}")
        return ""


def create_google_calendar_event(user, appointment):
    """
    Create a Google Calendar event using user's OAuth credentials.
    
    Args:
        user: Django User instance with google_credentials
        appointment: Appointment model instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import json
        from datetime import datetime
        from google.oauth2.credentials import Credentials as GoogleCredentials
        from googleapiclient.discovery import build as google_build
        
        # Check if user has Google credentials
        cred_obj = getattr(user, 'google_credentials', None)
        if not cred_obj or not cred_obj.credentials:
            logger.warning(f"User {user.id} has no Google credentials")
            return False
        
        # Load credentials
        cred_data = json.loads(cred_obj.credentials)
        creds = GoogleCredentials.from_authorized_user_info(
            cred_data, 
            scopes=['https://www.googleapis.com/auth/calendar.events']
        )
        
        # Build service
        service = google_build('calendar', 'v3', credentials=creds)
        
        # Prepare event
        try:
            start_dt = timezone.make_aware(datetime.combine(appointment.slot.date, appointment.slot.time))
        except Exception:
            start_dt = datetime.combine(appointment.slot.date, appointment.slot.time)
            start_dt = timezone.make_aware(start_dt)
        
        end_dt = start_dt + timedelta(minutes=appointment.duration_minutes or 60)
        
        event = {
            'summary': f"MindSettler Session - {appointment.full_name}",
            'description': appointment.location_details or 'MindSettler session',
            'start': {'dateTime': start_dt.isoformat()},
            'end': {'dateTime': end_dt.isoformat()},
        }
        
        # Insert event
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Created Google Calendar event {created_event.get('id')} for appointment {appointment.id}")
        return True
        
    except ImportError:
        logger.warning("Google API libraries not available")
        return False
    except Exception as e:
        logger.error(f"Error creating Google Calendar event for appointment {appointment.id}: {str(e)}")
        return False


def validate_appointment_slot(slot):
    """
    Validate if a slot is available for booking.
    
    Args:
        slot: SessionSlot model instance
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    from datetime import date as date_class
    
    # Check if slot is in the past
    if slot.date < date_class.today():
        return (False, "Cannot book appointments in the past")
    
    # Check if slot is available
    if not slot.is_available:
        return (False, "This slot is already booked")
    
    return (True, "")
