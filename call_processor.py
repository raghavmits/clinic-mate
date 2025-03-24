"""
Functions for handling call termination and post-call processing.
"""

import logging
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import re

import database  # Import the database module
from api import ClinicMateFunctions  # Import for type hints

logger = logging.getLogger("call-processor")
logger.setLevel(logging.INFO)

async def process_call_end(patient_data: Dict[str, Any]) -> str:
    """
    Process the end of a call by finalizing patient data and generating a call summary.
    
    Args:
        patient_data: Dictionary containing patient information collected during the call
        
    Returns:
        A summary string of actions taken
    """
    logger.info(f"Processing end of call for patient: {patient_data.get('patient_name', 'Unknown')}")
    
    actions_taken = []
    
    # Validate that required data has been collected
    missing_fields = check_required_fields(patient_data)
    if missing_fields:
        actions_taken.append(f"WARNING: Registration incomplete. Missing data: {', '.join(missing_fields)}")
    else:
        # Save patient data to database if all required information is available
        patient = await save_to_database(patient_data)
        if patient:
            actions_taken.append(f"Patient data saved to database with ID: {patient.id}")
    
    # Save patient data to log
    success = await save_patient_data(patient_data)
    if success:
        actions_taken.append("Patient data saved to log")
    
    # Generate and save call summary
    summary = generate_call_summary(patient_data)
    if summary:
        actions_taken.append("Call summary generated")
    
    # Send confirmation notification
    if patient_data.get('email'):
        sent = await send_confirmation_email(patient_data)
        if sent:
            actions_taken.append(f"Confirmation email sent to {patient_data['email']}")
    
    return "\n".join(actions_taken)

def check_required_fields(patient_data: Dict[str, Any]) -> List[str]:
    """
    Check if all required fields are filled.
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        List of missing field names
    """
    required_fields = {
        'patient_name': 'Name',
        'date_of_birth': 'Date of Birth',
        'insurance_provider': 'Insurance Provider',
        'insurance_id': 'Insurance ID',
        'medical_complaint': 'Reason for Visit',
        'address': 'Address',
        'phone_number': 'Phone Number'
    }
    
    missing = []
    
    for field, display_name in required_fields.items():
        if not patient_data.get(field):
            missing.append(display_name)
    
    return missing

async def save_to_database(patient_data: Dict[str, Any]) -> Optional[database.PatientRead]:
    """
    Save patient information to the database by creating a new record.
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        PatientRead object if successful, None otherwise
    """
    try:
        # Validate required fields for database storage
        name = patient_data.get('patient_name')
        dob_str = patient_data.get('date_of_birth')
        
        if not name or not dob_str:
            logger.warning(f"Cannot save to database: Missing name or date of birth")
            return None
            
        # Simplified date parsing - try common formats
        try:
            try:
                # MM/DD/YYYY format
                dob = datetime.strptime(dob_str, '%m/%d/%Y').date()
            except ValueError:
                try:
                    # Try YYYY-MM-DD format
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    # Try descriptive format (e.g., "January 15, 1980")
                    dob = datetime.strptime(dob_str, '%B %d, %Y').date()
        except Exception:
            logger.error(f"Could not parse date of birth: {dob_str}")
            # Use current date as fallback
            dob = datetime.now().date()
        
        # Always create a new patient record - simplified approach
        new_patient = database.PatientCreate(
            name=name,
            date_of_birth=dob,
            email=patient_data.get('email'),
            phone=patient_data.get('phone_number'),
            address=patient_data.get('address'),
            insurance_provider=patient_data.get('insurance_provider'),
            insurance_id=patient_data.get('insurance_id'),
            has_referral=patient_data.get('has_referral'),
            referred_physician=patient_data.get('referred_physician'),
            medical_complaint=patient_data.get('medical_complaint')
        )
        
        created_patient = await database.add_patient(new_patient)
        logger.info(f"Created new patient with ID: {created_patient.id}")
        return created_patient
            
    except Exception as e:
        logger.error(f"Error saving patient to database: {str(e)}")
        return None

async def save_patient_data(patient_data: Dict[str, Any]) -> bool:
    """
    Save patient data to the log.
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Log the data
        logger.info(f"Saving patient data: {patient_data}")
        
        # Simulate database operation with a short delay
        await asyncio.sleep(0.5)
        
        # Log a timestamp of when the data was saved
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Patient data saved at: {timestamp}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving patient data: {str(e)}")
        return False

def generate_call_summary(patient_data: Dict[str, Any]) -> str:
    """
    Generate a readable call summary from patient data
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        Formatted call summary as a string
    """
    # Get patient name, with fallback to "Unknown" if not present
    patient_name = patient_data.get('patient_name', 'Unknown')
    
    # Start building the summary
    summary = "# CLINIC-MATE CALL SUMMARY\n\n"
    
    # Check if we have critical patient information
    has_name = patient_data.get('patient_name') and patient_data['patient_name'].strip() != ""
    has_dob = patient_data.get('date_of_birth') and patient_data['date_of_birth'].strip() != ""
    
    # Add warning if critical information is missing
    if not has_name or not has_dob:
        summary += "⚠️ **WARNING: INCOMPLETE PATIENT RECORD** ⚠️\n"
        summary += "The following critical information is missing:\n"
        if not has_name:
            summary += "- Patient name\n"
        if not has_dob:
            summary += "- Date of birth\n"
        summary += "\nThis patient record may not have been saved to the database properly.\n\n"
    
    # Add patient information section
    summary += "PATIENT INFORMATION\n"
    summary += f"- Name: {patient_name}\n"
    
    if has_dob:
        summary += f"- Date of Birth: {patient_data.get('date_of_birth', 'Not provided')}\n"
    else:
        summary += f"- Date of Birth: Not provided\n"
    
    if patient_data.get('phone_number'):
        summary += f"- Phone: {patient_data['phone_number']}\n"
    
    if patient_data.get('email'):
        summary += f"- Email: {patient_data['email']}\n"
    
    if patient_data.get('address'):
        summary += f"- Address: {patient_data['address']}\n"
    
    # Add database information if available
    if patient_data.get('patient_id'):
        summary += f"- Patient ID: {patient_data['patient_id']} (Successfully saved to database)\n"
    else:
        if has_name and has_dob:
            summary += "- Database Status: Not saved to database (Error occurred)\n"
        else:
            summary += "- Database Status: Not saved to database (Missing required information)\n"
    
    # Add insurance section if available
    if any(k in patient_data for k in ['insurance_provider', 'insurance_id', 'has_referral']):
        summary += "\nINSURANCE INFORMATION\n"
        
        if patient_data.get('insurance_provider'):
            summary += f"- Provider: {patient_data['insurance_provider']}\n"
        
        if patient_data.get('insurance_id'):
            summary += f"- Insurance ID: {patient_data['insurance_id']}\n"
        
        if 'has_referral' in patient_data:
            referral_status = "Yes" if patient_data['has_referral'] else "No"
            summary += f"- Has Referral: {referral_status}\n"
            
            if patient_data.get('has_referral') and patient_data.get('referred_physician'):
                summary += f"- Referred By: {patient_data['referred_physician']}\n"
    
    # Add medical complaint if available
    if patient_data.get('medical_complaint'):
        summary += "\nMEDICAL INFORMATION\n"
        summary += f"- Complaint: {patient_data['medical_complaint']}\n"
    
    # Add appointment information if available
    # Check both wants_appointment and appointment_details since sometimes appointment details
    # exist even when wants_appointment is not set to True
    has_appointment_info = (patient_data.get('wants_appointment') or 
                           patient_data.get('appointment_details') or 
                           patient_data.get('doctor_preference') or
                           patient_data.get('specialty_preference'))
    
    if has_appointment_info:
        summary += "\nAPPOINTMENT INFORMATION\n"
        
        # Case 1: We have a confirmed appointment with details and ID
        if patient_data.get('appointment_id') and patient_data.get('appointment_details'):
            details = patient_data['appointment_details']
            summary += f"- Status: Appointment successfully booked\n"
            summary += f"- Appointment ID: {patient_data['appointment_id']}\n"
            
            if isinstance(details, dict):
                # Try different possible date/time formats based on actual data structure
                date_time = None
                if details.get('date_time'):
                    date_time = details['date_time']
                elif details.get('date') and details.get('time'):
                    date_time = f"{details['date']} at {details['time']}"
                
                if date_time:
                    summary += f"- Date & Time: {date_time}\n"
                
                # Doctor information with different possible structures
                doctor_name = None
                doctor_specialty = None
                
                # Handle doctor information in different possible formats
                if details.get('doctor'):
                    doctor_dict = details['doctor']
                    if isinstance(doctor_dict, dict):
                        doctor_name = doctor_dict.get('name')
                        doctor_specialty = doctor_dict.get('specialty')
                elif details.get('doctor_name'):
                    doctor_name = details['doctor_name']
                
                if doctor_name:
                    summary += f"- Doctor: {doctor_name}\n"
                
                # Specialty information
                if doctor_specialty:
                    summary += f"- Specialty: {doctor_specialty}\n"
                elif details.get('specialty'):
                    summary += f"- Specialty: {details['specialty']}\n"
                
                # Location information
                if details.get('location'):
                    summary += f"- Location: {details['location']}\n"
                else:
                    summary += f"- Location: Assort Medical Clinic Main Campus\n"
                
                # Duration information if available
                if details.get('duration_minutes'):
                    summary += f"- Duration: {details['duration_minutes']} minutes\n"
            else:
                # If appointment_details is not a dictionary, just include it as is
                summary += f"- Details: {details}\n"
        
        # Case 2: Appointment is pending/requested but not confirmed
        elif patient_data.get('appointment_details') and isinstance(patient_data['appointment_details'], dict):
            details = patient_data['appointment_details']
            status = details.get('status', 'pending')
            summary += f"- Status: Appointment {status}\n"
            
            # Try to get doctor information
            doctor_name = None
            doctor_specialty = None
            
            if details.get('doctor') and isinstance(details['doctor'], dict):
                doctor_dict = details['doctor']
                doctor_name = doctor_dict.get('name')
                doctor_specialty = doctor_dict.get('specialty')
            
            # Get date and time
            date_time = details.get('date_time')
            if date_time:
                summary += f"- Requested Date & Time: {date_time}\n"
            
            if doctor_name:
                summary += f"- Requested Doctor: {doctor_name}\n"
            
            if doctor_specialty:
                summary += f"- Specialty: {doctor_specialty}\n"
            
            # Add error information if present
            if details.get('error'):
                summary += f"- Note: Appointment scheduling needs follow-up: {details['error']}\n"
            
            summary += "- The clinic will contact you to confirm your appointment details.\n"
        
        # Case 3: Patient indicated preferences but no appointment was created
        elif patient_data.get('specialty_preference') or patient_data.get('doctor_preference'):
            summary += "- Status: Appointment requested but not confirmed\n"
            
            if patient_data.get('specialty_preference'):
                summary += f"- Preferred Specialty: {patient_data['specialty_preference']}\n"
            
            if patient_data.get('doctor_preference'):
                summary += f"- Preferred Doctor: {patient_data['doctor_preference']}\n"
            
            summary += "- The clinic will contact you to schedule your appointment.\n"
        
        # Case 4: Basic interest in appointments but no details
        else:
            summary += "- Status: Patient expressed interest in appointment, but no details provided\n"
            summary += "- Please call back to schedule a specific appointment.\n"
        
        # Add reminder
        summary += "- Please arrive 15 minutes early and bring your insurance card and ID.\n"
    
    # Add registration status
    summary += "\nREGISTRATION STATUS\n"
    if patient_data.get('is_registered'):
        summary += "- Status: Completed\n"
    else:
        stage = patient_data.get('registration_stage', 'Not started')
        summary += f"- Status: In progress ({stage})\n"
    
    # Add timestamp
    summary += f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return summary

async def send_confirmation_email(patient_data: Dict[str, Any]) -> bool:
    """
    Send a confirmation email to the patient.
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # In a real implementation, this would connect to an email service
        # For now, just log the action and simulate sending an email
        patient_name = patient_data.get('patient_name', 'Unknown')
        patient_email = patient_data.get('email')
        
        if not patient_email:
            logger.warning(f"Cannot send confirmation email - no email provided for {patient_name}")
            return False
        
        logger.info(f"Sending confirmation email to: {patient_email}")
        
        # Check if registration is complete before sending confirmation
        missing_fields = check_required_fields(patient_data)
        if missing_fields:
            logger.warning(f"Sending incomplete registration email - missing: {', '.join(missing_fields)}")
        
        # Simulate email sending operation with a short delay
        await asyncio.sleep(1.0)
        
        # Log a timestamp of when the email was sent
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Confirmation email sent at: {timestamp}")
        
        return True
    except Exception as e:
        logger.error(f"Error sending confirmation email: {str(e)}")
        return False

def extract_data_from_conversation(conversation: list[dict], data_type: str) -> Optional[str]:
    """
    Extract specific patient information from conversation history
    
    Args:
        conversation: List of conversation messages
        data_type: Type of data to extract ('name' or 'dob')
        
    Returns:
        Extracted information or None if not found
    """
    patterns = {
        'name': [
            r"[Mm]y name is ([A-Za-z\s.',-]+)",
            r"[Nn]ame is ([A-Za-z\s.',-]+)",
            r"[Nn]ame: ([A-Za-z\s.',-]+)",
            r"[Cc]all me ([A-Za-z\s.',-]+)",
            r"[Tt]his is ([A-Za-z\s.',-]+)"
        ],
        'dob': [
            r"[Bb]orn on (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"[Bb]irthday is (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"[Dd]ate of [Bb]irth:? (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"[Bb]irth date:? (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"[Dd][Oo][Bb]:? (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"[Bb]orn (?:on|in) ([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})",
            r"[Bb]orn (?:on|in) ([A-Za-z]+ \d{1,2},? \d{4})"
        ]
    }
    
    if data_type not in patterns:
        logger.warning(f"Unknown data type for extraction: {data_type}")
        return None
    
    # Only process user messages
    user_messages = [msg["content"] for msg in conversation if msg.get("role") == "user"]
    
    for message in user_messages:
        for pattern in patterns[data_type]:
            match = re.search(pattern, message)
            if match:
                extracted = match.group(1).strip()
                logger.info(f"Extracted {data_type} from conversation: {extracted}")
                return extracted
    
    logger.warning(f"Could not extract {data_type} from conversation history")
    return None

async def process_call_end_from_context(
    fnc_ctx: ClinicMateFunctions, 
    patient_id: Optional[int] = None, 
    log_queue: Optional[asyncio.Queue] = None
) -> Tuple[Optional[int], str, bool]:
    """
    Process end-of-call tasks directly from function context, including data saving and summary generation
    
    Args:
        fnc_ctx: The ClinicMateFunctions context with collected patient information
        patient_id: Optional existing patient ID if already saved
        log_queue: Optional async queue for logging
        
    Returns:
        Tuple containing (updated_patient_id, call_summary, success_status)
    """
    logger.info("Processing end of call tasks from context")
    
    # Log the current patient name and DOB for debugging
    logger.info(f"Patient name from context: {fnc_ctx.patient_name}")
    logger.info(f"Patient DOB from context: {fnc_ctx.date_of_birth}")
    
    # Try to extract missing patient name and DOB from conversation if they're not in the context
    if (not fnc_ctx.patient_name or fnc_ctx.patient_name.strip() == "") and hasattr(fnc_ctx, 'conversation_history'):
        extracted_name = extract_data_from_conversation(fnc_ctx.conversation_history, 'name')
        if extracted_name:
            fnc_ctx.patient_name = extracted_name
            logger.info(f"Recovered patient name from conversation: {extracted_name}")
    
    if (not fnc_ctx.date_of_birth or fnc_ctx.date_of_birth.strip() == "") and hasattr(fnc_ctx, 'conversation_history'):
        extracted_dob = extract_data_from_conversation(fnc_ctx.conversation_history, 'dob')
        if extracted_dob:
            fnc_ctx.date_of_birth = extracted_dob
            logger.info(f"Recovered patient DOB from conversation: {extracted_dob}")
    
    # Convert function context to dictionary format
    patient_data = {
        'patient_name': fnc_ctx.patient_name,
        'date_of_birth': fnc_ctx.date_of_birth,
        'insurance_provider': fnc_ctx.insurance_provider,
        'insurance_id': fnc_ctx.insurance_id,
        'has_referral': fnc_ctx.has_referral,
        'referred_physician': fnc_ctx.referred_physician,
        'medical_complaint': fnc_ctx.medical_complaint,
        'address': fnc_ctx.address,
        'phone_number': fnc_ctx.phone_number,
        'email': fnc_ctx.email,
        'is_registered': fnc_ctx.is_registered,
        'registration_stage': fnc_ctx.registration_stage,
        # Include appointment information
        'wants_appointment': fnc_ctx.wants_appointment,
        'specialty_preference': fnc_ctx.specialty_preference,
        'doctor_preference': fnc_ctx.doctor_preference,
        'appointment_id': fnc_ctx.appointment_id
    }
    
    # Add appointment details if they exist
    if hasattr(fnc_ctx, 'appointment_details') and fnc_ctx.appointment_details:
        patient_data['appointment_details'] = fnc_ctx.appointment_details
        logger.info(f"Including appointment details in call summary: {fnc_ctx.appointment_details}")
    
    # Try to save the patient to the database if we have the necessary info
    if patient_id is None:
        # Check if we have name and DOB
        have_name = fnc_ctx.patient_name is not None and fnc_ctx.patient_name.strip() != ""
        have_dob = fnc_ctx.date_of_birth is not None and fnc_ctx.date_of_birth.strip() != ""
        
        if have_name and have_dob:
            # Check if patient_id is stored in the function context
            if hasattr(fnc_ctx, 'database_patient_id') and fnc_ctx.database_patient_id:
                patient_id = fnc_ctx.database_patient_id
                logger.info(f"Using existing patient ID from context: {patient_id}")
            else:
                try:
                    patient_id = await database.save_patient_from_context(fnc_ctx)
                    if patient_id:
                        patient_data['patient_id'] = patient_id
                        logger.info(f"Patient saved to database with ID: {patient_id}")
                    else:
                        logger.warning("Failed to save patient to database at end of call")
                except Exception as e:
                    logger.error(f"Error saving patient to database at end of call: {str(e)}")
        else:
            logger.warning(f"Cannot save patient to database: Missing name ({have_name}) or date of birth ({have_dob})")
    
    # If we have an appointment ID but not the details, try to fetch them now
    if fnc_ctx.appointment_id and not fnc_ctx.appointment_details:
        try:
            appointment_details = await database.get_appointment_details(fnc_ctx.appointment_id)
            if appointment_details:
                patient_data['appointment_details'] = appointment_details
                logger.info(f"Retrieved appointment details for ID: {fnc_ctx.appointment_id}")
        except Exception as e:
            logger.error(f"Error retrieving appointment details: {str(e)}")
    
    # Process the end of call using our regular process_call_end function
    summary = await process_call_end(patient_data)
    
    # Log the summary of actions taken if a log queue was provided
    if log_queue:
        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: End of call processing complete:\n{summary}\n\n")
    
    # Generate a call summary
    call_summary = generate_call_summary(patient_data)
    
    # Log the call summary if a log queue was provided
    if log_queue:
        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: CALL SUMMARY:\n{call_summary}\n\n")
    
    try:
        # Save the call summary to a separate file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        patient_name = fnc_ctx.patient_name or "unknown"
        filename = f"call_summary_{patient_name.replace(' ', '_')}_{timestamp}.txt"
        
        from aiofile import async_open as open
        async with open(filename, "w") as f:
            await f.write(call_summary)
            logger.info(f"Call summary saved to file: {filename}")
    except Exception as e:
        logger.error(f"Error saving call summary: {str(e)}")
    
    return patient_id, call_summary, True 