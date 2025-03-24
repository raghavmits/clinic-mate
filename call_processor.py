"""
Functions for handling call termination and post-call processing.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os

import database  # Import the database module
from api import ClinicMateFunctions  # Import for type hints
from utils import (
    generate_call_summary,
    create_email_message,
    generate_html_email,
    get_email_credentials,
    send_email_sync,
    extract_data_from_conversation,
    parse_date_of_birth
)

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
            
        # Parse the date of birth using our utility function
        dob = parse_date_of_birth(dob_str)
        if not dob:
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

async def send_confirmation_email(patient_data: Dict[str, Any]) -> bool:
    """
    Send a confirmation email to the patient with their call summary.
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Get patient information
        patient_name = patient_data.get('patient_name', 'Unknown')
        
        # Get email credentials from environment
        sender_email, password = get_email_credentials()
        # recipient_email = patient_data.get('email', os.environ.get("EMAIL_RECIPIENT"))
        recipient_email = os.environ.get("EMAIL_RECIPIENT")

        if not recipient_email:
            logger.warning(f"No email provided for {patient_name}, using default recipient")
            
        # If no password is set in environment variables, log an error
        if not sender_email or not password:
            logger.error("Email credentials not set in environment variables")
            return False
                    
        # Generate the call summary
        call_summary = generate_call_summary(patient_data)
                    
        # Create the HTML content
        html_content = generate_html_email(call_summary, "Assort Medical Clinic Call Summary")
        
        # Create plain text version as a fallback
        text_content = f"""
        CLINIC-MATE CALL SUMMARY
        
        {call_summary}
                
        This is an automated message from Clinic-Mate. Please do not reply to this email.
        © {datetime.now().year} Assort Clinic. All rights reserved.
        """
        
        # Create the email message
        message = create_email_message(
            subject=f"Clinic-Mate: Appointment Summary for {patient_name}",
            text_content=text_content,
            html_content=html_content,
            sender_email=sender_email,
            recipient_email=recipient_email
        )
        
        # Connect to the SMTP server and send the email
        logger.info(f"Attempting to send email to: {recipient_email}")
            
        # Use asyncio to run the blocking SMTP operations in a thread pool
        success = await asyncio.to_thread(
            send_email_sync,
            sender_email,
            password,
            recipient_email,
            message.as_string()
        )
        
        if not success:
            logger.error("Failed to send email")
            return False
                    
        # Log success
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Confirmation email sent at: {timestamp}")
        
        # Save a copy of the call summary to a file
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        patient_name_safe = patient_name.replace(" ", "_")
        filename = f"call_summary_{patient_name_safe}_{timestamp_file}.txt"
        
        # Write the file
        with open(filename, "w") as f:
            f.write(call_summary)
        
        logger.info(f"Call summary saved to file: {filename}")
        
        return True
    except Exception as e:
        logger.error(f"Error sending confirmation email: {str(e)}")
        return False

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
        have_name = bool(fnc_ctx.patient_name and fnc_ctx.patient_name.strip())
        have_dob = bool(fnc_ctx.date_of_birth and fnc_ctx.date_of_birth.strip())
        
        # If we're missing either name or DOB, try to extract them from conversation
        if not have_name or not have_dob:
            logger.warning(f"Missing critical patient data: Name: {have_name}, DOB: {have_dob}")
            
            # Try to extract missing name from conversation
            if not have_name and hasattr(fnc_ctx, 'conversation_history'):
                extracted_name = extract_data_from_conversation(fnc_ctx.conversation_history, 'name')
                if extracted_name:
                    fnc_ctx.patient_name = extracted_name
                    patient_data['patient_name'] = extracted_name
                    have_name = True
                    logger.info(f"Extracted patient name from conversation: {extracted_name}")
                    if log_queue:
                        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Extracted name from conversation: {extracted_name}\n\n")
            
            # Try to extract missing DOB from conversation
            if not have_dob and hasattr(fnc_ctx, 'conversation_history'):
                extracted_dob = extract_data_from_conversation(fnc_ctx.conversation_history, 'dob')
                if extracted_dob:
                    fnc_ctx.date_of_birth = extracted_dob
                    patient_data['date_of_birth'] = extracted_dob
                    have_dob = True
                    logger.info(f"Extracted patient DOB from conversation: {extracted_dob}")
                    if log_queue:
                        log_queue.put_nowait(f"[{datetime.now()}] SYSTEM: Extracted DOB from conversation: {extracted_dob}\n\n")
        
        # If we have the minimum required fields, save the patient
        if have_name and have_dob:
            try:
                # Check if patient_id is stored in the function context
                if hasattr(fnc_ctx, 'database_patient_id') and fnc_ctx.database_patient_id:
                    patient_id = fnc_ctx.database_patient_id
                    logger.info(f"Using existing patient ID from context: {patient_id}")
                else:
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
