"""
Functions for handling call termination and post-call processing.
"""

import logging
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple

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
    Generate a summary of the call based on patient data.
    
    Args:
        patient_data: Dictionary containing patient information
        
    Returns:
        A string containing the call summary
    """
    try:
        summary_parts = []
        
        # Add patient name and time
        patient_name = patient_data.get('patient_name', 'Unknown')
        summary_parts.append(f"Call summary for {patient_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if data collection is complete
        missing_fields = check_required_fields(patient_data)
        if missing_fields:
            summary_parts.append(f"\n⚠️ REGISTRATION INCOMPLETE - Missing information: {', '.join(missing_fields)}")
        else:
            summary_parts.append("\n✅ REGISTRATION COMPLETE - All required information collected")
        
        # Add data collected during call
        summary_parts.append("\nINFORMATION COLLECTED:")
        
        if patient_data.get('patient_name'):
            summary_parts.append(f"- Name: {patient_data['patient_name']}")
            
        if patient_data.get('date_of_birth'):
            summary_parts.append(f"- Date of Birth: {patient_data['date_of_birth']}")
            
        if patient_data.get('insurance_provider'):
            summary_parts.append(f"- Insurance: {patient_data['insurance_provider']} (ID: {patient_data.get('insurance_id', 'Not provided')})")
            
        if patient_data.get('has_referral'):
            if patient_data.get('referred_physician'):
                summary_parts.append(f"- Referral: Yes, to {patient_data['referred_physician']}")
            else:
                summary_parts.append("- Referral: Yes (physician not specified)")
        else:
            summary_parts.append("- Referral: No")
            
        if patient_data.get('medical_complaint'):
            summary_parts.append(f"- Reason for Visit: {patient_data['medical_complaint']}")
            
        if patient_data.get('address'):
            summary_parts.append(f"- Address: {patient_data['address']}")
            
        if patient_data.get('phone_number'):
            summary_parts.append(f"- Phone: {patient_data['phone_number']}")
            
        if patient_data.get('email'):
            summary_parts.append(f"- Email: {patient_data['email']}")
            
        # Add status
        if patient_data.get('is_registered'):
            summary_parts.append("\nSTATUS: Registration Complete")
        else:
            summary_parts.append("\nSTATUS: Registration Incomplete")
        
        # Add next steps
        if patient_data.get('is_registered'):
            summary_parts.append("\nNEXT STEPS: Patient should arrive 15 minutes before their scheduled appointment time.")
        else:
            summary_parts.append("\nNEXT STEPS: Patient needs to complete registration before their appointment.")
            
        # Join all parts into a full summary
        full_summary = "\n".join(summary_parts)
        
        # Log the summary
        logger.info(f"Generated call summary for {patient_name}")
        
        return full_summary
    except Exception as e:
        logger.error(f"Error generating call summary: {str(e)}")
        return f"Error generating call summary: {str(e)}"

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

# Function moved from agent.py to improve modularity

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
        'registration_stage': fnc_ctx.registration_stage
    }
    
    # If we haven't already saved to the database and we have the minimum required info, do it now
    if patient_id is None and fnc_ctx.patient_name and fnc_ctx.date_of_birth:
        try:
            patient_id = await database.save_patient_from_context(fnc_ctx)
            if patient_id:
                patient_data['patient_id'] = patient_id
                logger.info(f"Patient saved to database with ID: {patient_id}")
        except Exception as e:
            logger.error(f"Error saving patient to database at end of call: {str(e)}")
    
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