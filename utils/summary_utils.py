"""
Utility functions for generating summary information and reports.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger("summary-utils")
logger.setLevel(logging.INFO)

def generate_patient_info_section(patient_data: Dict[str, Any]) -> str:
    """
    Generate the patient information section of the summary
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        Formatted patient information section
    """
    patient_name = patient_data.get('patient_name', 'Unknown')
    
    # Check if we have critical patient information
    has_name = patient_data.get('patient_name') and patient_data['patient_name'].strip() != ""
    has_dob = patient_data.get('date_of_birth') and patient_data['date_of_birth'].strip() != ""
    
    summary = []
    
    # Add warning if critical information is missing
    if not has_name or not has_dob:
        summary.append("⚠️ **WARNING: INCOMPLETE PATIENT RECORD** ⚠️")
        summary.append("The following critical information is missing:")
        if not has_name:
            summary.append("- Patient name")
        if not has_dob:
            summary.append("- Date of birth")
        summary.append("\nThis patient record may not have been saved to the database properly.\n")
    
    # Add patient information section
    summary.append("PATIENT INFORMATION")
    summary.append(f"- Name: {patient_name}")
    
    if has_dob:
        summary.append(f"- Date of Birth: {patient_data.get('date_of_birth', 'Not provided')}")
    else:
        summary.append("- Date of Birth: Not provided")
    
    if patient_data.get('phone_number'):
        summary.append(f"- Phone: {patient_data['phone_number']}")
    
    if patient_data.get('email'):
        summary.append(f"- Email: {patient_data['email']}")
    
    if patient_data.get('address'):
        summary.append(f"- Address: {patient_data['address']}")
    
    # Add database information if available
    if patient_data.get('patient_id'):
        summary.append(f"- Patient ID: {patient_data['patient_id']} (Successfully saved to database)")
    else:
        if has_name and has_dob:
            summary.append("- Database Status: Not saved to database (Error occurred)")
        else:
            summary.append("- Database Status: Not saved to database (Missing required information)")
    
    return "\n".join(summary)

def generate_insurance_section(patient_data: Dict[str, Any]) -> str:
    """
    Generate the insurance information section of the summary
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        Formatted insurance information section
    """
    if not any(k in patient_data for k in ['insurance_provider', 'insurance_id', 'has_referral']):
        return ""
    
    summary = ["\nINSURANCE INFORMATION"]
    
    if patient_data.get('insurance_provider'):
        summary.append(f"- Provider: {patient_data['insurance_provider']}")
    
    if patient_data.get('insurance_id'):
        summary.append(f"- Insurance ID: {patient_data['insurance_id']}")
    
    if 'has_referral' in patient_data:
        referral_status = "Yes" if patient_data['has_referral'] else "No"
        summary.append(f"- Has Referral: {referral_status}")
        
        if patient_data.get('has_referral') and patient_data.get('referred_physician'):
            summary.append(f"- Referred By: {patient_data['referred_physician']}")
    
    return "\n".join(summary)

def generate_medical_section(patient_data: Dict[str, Any]) -> str:
    """
    Generate the medical information section of the summary
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        Formatted medical information section
    """
    if not patient_data.get('medical_complaint'):
        return ""
    
    summary = ["\nMEDICAL INFORMATION"]
    summary.append(f"- Complaint: {patient_data['medical_complaint']}")
    
    return "\n".join(summary)

def generate_appointment_section(patient_data: Dict[str, Any]) -> str:
    """
    Generate the appointment information section of the summary
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        Formatted appointment information section
    """
    # Check if we have any appointment information
    has_appointment_info = (patient_data.get('wants_appointment') or 
                           patient_data.get('appointment_details') or 
                           patient_data.get('doctor_preference') or
                           patient_data.get('specialty_preference'))
    
    if not has_appointment_info:
        return ""
    
    summary = ["\nAPPOINTMENT INFORMATION"]
    
    # Case 1: We have a confirmed appointment with details and ID
    if patient_data.get('appointment_id') and patient_data.get('appointment_details'):
        details = patient_data['appointment_details']
        summary.append("- Status: Appointment successfully booked")
        summary.append(f"- Appointment ID: {patient_data['appointment_id']}")
        
        if isinstance(details, dict):
            # Date and time
            date_time = None
            if details.get('date_time'):
                date_time = details['date_time']
            elif details.get('date') and details.get('time'):
                date_time = f"{details['date']} at {details['time']}"
            
            if date_time:
                summary.append(f"- Date & Time: {date_time}")
            
            # Doctor information
            doctor_name = None
            doctor_specialty = None
            
            if details.get('doctor'):
                doctor_dict = details['doctor']
                if isinstance(doctor_dict, dict):
                    doctor_name = doctor_dict.get('name')
                    doctor_specialty = doctor_dict.get('specialty')
            elif details.get('doctor_name'):
                doctor_name = details['doctor_name']
            
            if doctor_name:
                summary.append(f"- Doctor: {doctor_name}")
            
            # Specialty
            if doctor_specialty:
                summary.append(f"- Specialty: {doctor_specialty}")
            elif details.get('specialty'):
                summary.append(f"- Specialty: {details['specialty']}")
            
            # Location
            if details.get('location'):
                summary.append(f"- Location: {details['location']}")
            else:
                summary.append("- Location: Assort Medical Clinic Main Campus")
            
            # Duration
            if details.get('duration_minutes'):
                summary.append(f"- Duration: {details['duration_minutes']} minutes")
        else:
            # If not a dictionary, include as is
            summary.append(f"- Details: {details}")
    
    # Case 2: Appointment is pending/requested but not confirmed
    elif patient_data.get('appointment_details') and isinstance(patient_data['appointment_details'], dict):
        details = patient_data['appointment_details']
        status = details.get('status', 'pending')
        summary.append(f"- Status: Appointment {status}")
        
        # Date and time if available
        if details.get('date_time'):
            summary.append(f"- Requested Date & Time: {details['date_time']}")
        
        # Doctor name if available
        doctor_name = None
        if details.get('doctor') and isinstance(details['doctor'], dict):
            doctor_name = details['doctor'].get('name')
            doctor_specialty = details['doctor'].get('specialty')
            
            if doctor_name:
                summary.append(f"- Requested Doctor: {doctor_name}")
            
            if doctor_specialty:
                summary.append(f"- Specialty: {doctor_specialty}")
        
        # Error information if present
        if details.get('error'):
            summary.append(f"- Note: Appointment scheduling needs follow-up: {details['error']}")
        
        summary.append("- The clinic will contact you to confirm your appointment details.")
    
    # Case 3: Patient indicated preferences but no appointment was created
    elif patient_data.get('specialty_preference') or patient_data.get('doctor_preference'):
        summary.append("- Status: Appointment requested but not confirmed")
        
        if patient_data.get('specialty_preference'):
            summary.append(f"- Preferred Specialty: {patient_data['specialty_preference']}")
        
        if patient_data.get('doctor_preference'):
            summary.append(f"- Preferred Doctor: {patient_data['doctor_preference']}")
        
        summary.append("- The clinic will contact you to schedule your appointment.")
    
    # Case 4: Basic interest in appointments but no details
    else:
        summary.append("- Status: Patient expressed interest in appointment, but no details provided")
        summary.append("- Please call back to schedule a specific appointment.")
    
    # Add reminder for all appointment cases
    summary.append("- Please arrive 15 minutes early and bring your insurance card and ID.")
    
    return "\n".join(summary)

def generate_registration_status(patient_data: Dict[str, Any]) -> str:
    """
    Generate the registration status section of the summary
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        Formatted registration status section
    """
    summary = ["\nREGISTRATION STATUS"]
    
    if patient_data.get('is_registered'):
        summary.append("- Status: Completed")
    else:
        stage = patient_data.get('registration_stage', 'Not started')
        summary.append(f"- Status: In progress ({stage})")
    
    return "\n".join(summary)

def generate_call_summary(patient_data: Dict[str, Any]) -> str:
    """
    Generate a complete call summary from patient data by combining all sections
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        Formatted call summary as a string
    """
    # Start with header
    sections = ["Thank you for calling Assort Medical Clinic. Here is a summary of your call: \n"]
    
    # Add each section
    sections.append(generate_patient_info_section(patient_data))
    
    insurance_section = generate_insurance_section(patient_data)
    if insurance_section:
        sections.append(insurance_section)
    
    medical_section = generate_medical_section(patient_data)
    if medical_section:
        sections.append(medical_section)
    
    appointment_section = generate_appointment_section(patient_data)
    if appointment_section:
        sections.append(appointment_section)
    
    sections.append(generate_registration_status(patient_data))
    
    # Add timestamp
    sections.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Combine all sections
    return "\n".join(sections) 