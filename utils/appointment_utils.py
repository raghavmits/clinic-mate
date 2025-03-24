"""
Utility functions for handling appointment-related operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger("appointment-utils")
logger.setLevel(logging.INFO)

def format_appointment_details(appointment_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format appointment details for consistent structure throughout the application
    
    Args:
        appointment_details: Raw appointment details
        
    Returns:
        Formatted appointment details with consistent structure
    """
    if not appointment_details:
        return {}
    
    formatted = {}
    
    # Extract date and time
    if appointment_details.get('date_time'):
        formatted['date_time'] = appointment_details['date_time']
    elif appointment_details.get('date') and appointment_details.get('time'):
        formatted['date_time'] = f"{appointment_details['date']} at {appointment_details['time']}"
    
    # Extract doctor information
    doctor = {}
    if appointment_details.get('doctor') and isinstance(appointment_details['doctor'], dict):
        doctor = appointment_details['doctor']
    else:
        if appointment_details.get('doctor_name'):
            doctor['name'] = appointment_details['doctor_name']
        if appointment_details.get('doctor_id'):
            doctor['id'] = appointment_details['doctor_id']
    
    # Add specialty information
    if doctor.get('specialty'):
        formatted['specialty'] = doctor['specialty']
    elif appointment_details.get('specialty'):
        formatted['specialty'] = appointment_details['specialty']
    
    if doctor:
        formatted['doctor'] = doctor
    
    # Add status
    if appointment_details.get('status'):
        formatted['status'] = appointment_details['status']
    else:
        formatted['status'] = 'scheduled'
    
    # Add duration
    if appointment_details.get('duration_minutes'):
        formatted['duration_minutes'] = appointment_details['duration_minutes']
    else:
        formatted['duration_minutes'] = 30
    
    # Add location
    if appointment_details.get('location'):
        formatted['location'] = appointment_details['location']
    else:
        formatted['location'] = 'Assort Medical Clinic Main Campus'
    
    # Copy any error information
    if appointment_details.get('error'):
        formatted['error'] = appointment_details['error']
    
    # Copy ID if available
    if appointment_details.get('id'):
        formatted['id'] = appointment_details['id']
    
    return formatted

def create_pending_appointment(
    doctor_name: str, 
    specialty: str, 
    date_time_str: str, 
    error_message: str = None
) -> Dict[str, Any]:
    """
    Create a pending appointment when full booking fails
    
    Args:
        doctor_name: Name of the requested doctor
        specialty: Medical specialty
        date_time_str: Requested date/time as string
        error_message: Optional error message to include
        
    Returns:
        Appointment details dictionary with pending status
    """
    appointment = {
        'doctor': {'name': doctor_name or 'Unknown Doctor', 'specialty': specialty or 'Unknown Specialty'},
        'date_time': date_time_str,
        'duration_minutes': 30,
        'status': 'pending',
        'location': 'Assort Medical Clinic Main Campus'
    }
    
    if error_message:
        appointment['error'] = error_message
    
    return appointment

def should_suggest_alternative_doctor(
    error_type: str, 
    specialty: str
) -> bool:
    """
    Determine whether to suggest an alternative doctor based on error type
    
    Args:
        error_type: Type of error encountered when booking
        specialty: Medical specialty requested
        
    Returns:
        True if an alternative doctor should be suggested, False otherwise
    """
    # If the doctor doesn't exist or is not found, suggest alternatives
    if error_type.lower() in ['not found', 'doctor not found', 'no such doctor']:
        return True
    
    # If there are no available slots, suggest alternatives
    if error_type.lower() in ['no available slots', 'fully booked']:
        return True
    
    # Default to not suggesting
    return False

def format_time_slots(time_slots: List[datetime]) -> str:
    """
    Format a list of time slots for display
    
    Args:
        time_slots: List of datetime objects representing available slots
        
    Returns:
        Formatted string listing the available time slots
    """
    if not time_slots:
        return "No available time slots found."
    
    formatted_slots = []
    for slot in time_slots:
        formatted_slots.append(f"- {slot.strftime('%A, %B %d, %Y at %I:%M %p')}")
    
    return "\n".join(formatted_slots)

def create_confirmation_message(appointment_details: Dict[str, Any]) -> str:
    """
    Create a confirmation message for an appointment
    
    Args:
        appointment_details: Appointment details dictionary
        
    Returns:
        Formatted confirmation message
    """
    doctor_name = "Unknown Doctor"
    specialty = "Unknown Specialty"
    date_time = "Unknown Date/Time"
    
    if appointment_details.get('doctor'):
        if isinstance(appointment_details['doctor'], dict):
            doctor_name = appointment_details['doctor'].get('name', doctor_name)
            specialty = appointment_details['doctor'].get('specialty', specialty)
    
    if appointment_details.get('date_time'):
        date_time = appointment_details['date_time']
    
    status = appointment_details.get('status', 'scheduled')
    
    if status == 'scheduled':
        return (f"Great news! I've successfully booked your appointment with {doctor_name}, "
                f"our {specialty} specialist, for {date_time}. The appointment will last "
                f"approximately 30 minutes. Please arrive 15 minutes early with your "
                f"insurance card and ID.")
    else:
        return (f"I've scheduled your appointment with {doctor_name} for {date_time}. "
                f"There was a small issue with our system, but your appointment request "
                f"has been recorded. Our scheduling team will contact you to confirm.") 