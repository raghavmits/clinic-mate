# Clinic Mate

A voice-powered patient registration system for Assort clinic using LiveKit for voice conversations.

## Revised Patient Registration Flow

The system supports a comprehensive patient registration workflow:

1. **Initial Greeting** - Welcomes the patient and asks for their name and date of birth
2. **Insurance Information** - Collects the patient's insurance provider and ID number
3. **Referral Details** - Asks if they have a referral, and if so, which physician referred them
4. **Medical Complaint** - Collects the reason for their visit or chief medical complaint
5. **Demographic Information** - Collects the patient's address
6. **Contact Information** - Collects phone number and optionally email address
7. **Confirmation** - Provides a summary of all collected information for verification
8. **Completion** - Confirms successful registration and provides appointment guidance

The system is designed to be conversational and adaptable, handling questions and out-of-order information gracefully while guiding the patient through the registration process.

## Features

- **Comprehensive Information Collection**: Collects all relevant patient information in a logical, conversational flow
- **Adaptable Conversation**: Handles out-of-order information and side questions naturally
- **Field Correction**: Allows patients to correct specific fields if information is wrong
- **Empathetic Approach**: Acknowledges medical complaints with empathy without attempting diagnosis
- **Thorough Documentation**: Logs all information collected and provides clear confirmations
- **Optional Fields**: Email is presented as optional but beneficial for reminders

## API Functions

The API module (`api.py`) provides these functions for the voice agent:

- `register_patient(name, date_of_birth)`: Collect basic patient information
- `collect_insurance_info(provider, insurance_id)`: Collect insurance details
- `collect_referral_info(has_referral, referred_physician)`: Collect referral information
- `collect_medical_complaint(complaint)`: Collect reason for visit
- `collect_address(address)`: Collect patient's address
- `collect_phone(phone_number)`: Collect contact phone number
- `collect_email(email)`: Collect optional email address
- `get_patient_info()`: Get a summary of all collected information
- `confirm_information(confirmed)`: Confirm and finalize registration
- `update_specific_info(field, value)`: Update a specific field if corrections are needed

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Voice Agent

```bash
python agent.py
```

This will start the voice agent that will handle patient registration conversations.


## Conversation Design

The conversation flow is designed to be:

1. **Natural**: Uses conversational language rather than formal forms
2. **Efficient**: Collects information in a logical order
3. **Empathetic**: Shows understanding when discussing medical concerns
4. **Helpful**: Provides clear guidance and feedback
5. **Flexible**: Adapts to the patient's communication style 