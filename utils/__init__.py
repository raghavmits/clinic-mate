"""
Utilities package for the Clinic-Mate application.
"""

from utils.date_utils import (
    parse_date_time,
    format_date_for_display,
    is_date_in_future,
    parse_date_of_birth
)

from utils.email_utils import (
    create_email_message,
    generate_html_email,
    get_email_credentials,
    send_email_sync
)

from utils.summary_utils import (
    generate_patient_info_section,
    generate_insurance_section,
    generate_medical_section,
    generate_appointment_section,
    generate_registration_status,
    generate_call_summary
)

from utils.extraction_utils import (
    extract_data_from_conversation,
    extract_multiple_data_types,
    extract_all_patient_data,
    clean_extracted_data
)

from utils.appointment_utils import (
    format_appointment_details,
    create_pending_appointment,
    should_suggest_alternative_doctor,
    format_time_slots,
    create_confirmation_message
)

__all__ = [
    # Date utilities
    'parse_date_time', 'format_date_for_display', 'is_date_in_future', 'parse_date_of_birth',
    
    # Email utilities
    'create_email_message', 'generate_html_email', 'get_email_credentials', 'send_email_sync',
    
    # Summary utilities
    'generate_patient_info_section', 'generate_insurance_section', 'generate_medical_section',
    'generate_appointment_section', 'generate_registration_status', 'generate_call_summary',
    
    # Extraction utilities
    'extract_data_from_conversation', 'extract_multiple_data_types', 'extract_all_patient_data',
    'clean_extracted_data',
    
    # Appointment utilities
    'format_appointment_details', 'create_pending_appointment', 
    'should_suggest_alternative_doctor', 'format_time_slots', 'create_confirmation_message'
] 