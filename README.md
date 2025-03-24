# Clinic Mate

A robust voice-powered patient registration and appointment booking system for Assort clinic using LiveKit for natural voice conversations.

## Core Functionality

Clinic Mate is designed to streamline the patient registration and appointment booking process through an intelligent voice assistant that:

1. **Registers New Patients** - Collects and validates patient data with robust error handling
2. **Books Appointments** - Matches patients with appropriate specialists using intelligent specialty mapping
3. **Handles Edge Cases** - Maintains conversation flow even when information is incomplete or provided out of order
4. **Generates Summaries** - Creates detailed call summaries with patient information and appointment details
5. **Stores Information** - Securely stores patient data and appointment details in a database
6. **Sends Confirmations** - Emails appointment summaries to patients with all relevant details

## Patient Registration Flow

The system facilitates a comprehensive patient registration workflow:

1. **Initial Greeting** - Welcomes the patient and asks for their name and date of birth
2. **Insurance Information** - Collects the patient's insurance provider and ID number
3. **Referral Details** - Asks if they have a referral, and if so, which physician referred them
4. **Medical Complaint** - Collects the reason for their visit or chief medical complaint
5. **Demographic Information** - Collects the patient's address
6. **Contact Information** - Collects phone number and optionally email address
7. **Confirmation** - Provides a summary of all collected information for verification
8. **Completion** - Confirms successful registration and provides appointment guidance

## Appointment Booking Process

After registration, the system offers a seamless appointment booking experience:

1. **Specialty Selection** - Suggests appropriate specialties based on the patient's medical complaint
2. **Doctor Selection** - Presents available doctors within the chosen specialty with their bios
3. **Appointment Scheduling** - Shows available time slots and confirms the patient's preferred time
4. **Appointment Confirmation** - Provides booking confirmation with appointment details
5. **Reminder Options** - Offers to send appointment details to the patient's email or phone

## Advanced Features

- **Intelligent Specialty Matching**: Uses a comprehensive mapping system to match medical complaints with appropriate specialties, including handling of abbreviations and alternative terms
- **Flexible Doctor Matching**: Finds doctors even with partial names or when titles like "Dr." are included or omitted
- **Robust Date/Time Parsing**: Handles various date and time formats including natural language inputs
- **Fallback Handling**: Creates pending appointments when exact matching fails, ensuring no patient requests are lost
- **Error Recovery**: Gracefully handles missing or invalid data without disrupting the conversation flow
- **Comprehensive Call Summaries**: Generates detailed summaries including patient information, insurance details, and appointment information
- **Email Confirmations**: Sends beautifully formatted HTML emails with appointment details and clinic information

## Technical Implementation

### Database Structure

The system uses SQLModel (SQLAlchemy + Pydantic) for type-safe database interactions with the following models:
- **Patient**: Stores patient demographic and insurance information
- **Specialty**: Catalogs medical specialties with descriptions
- **Doctor**: Links doctors to their specialties with biographical information
- **Appointment**: Tracks scheduled appointments with status information
- **DoctorAvailability**: Manages doctor availability slots

### Helper Functions

Intelligent matching is implemented through specialized helper functions:
- **find_doctor_by_name**: Flexibly matches doctor names using partial name matching
- **find_specialty_by_name**: Maps medical complaints to specialties using comprehensive term mapping
- **parse_date_time**: Handles multiple date/time formats for appointment scheduling

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create the sample data (specialties, doctors and availabilities)
python scripts/create_sample_data.py

# Set up email credentials (for appointment confirmations)
export EMAIL_PASSWORD='your_app_password'
```

For detailed email setup instructions, see [Email Setup Guide](docs/email_setup.md).

## Usage

### Running the Voice Agent

```bash
# Development mode
python agent.py dev

# Production mode
python agent.py start
```

### Testing Appointment Summaries

```bash
# Generate test appointment summaries
python generate_test_summary.py
```

## Available Medical Specialties

The system includes doctors in the following specialties:

- **Cardiology**: Heart and blood vessel disorders
- **Ophthalmology**: Eye disorders and vision care
- **Otolaryngology (ENT)**: Ear, nose, and throat disorders
- **Orthopedics**: Bone and joint disorders
- **Neurology**: Brain, spinal cord, and nerve disorders
- **Dermatology**: Skin disorders
- **Pulmonology**: Lung and respiratory disorders
- **Gastroenterology**: Digestive system disorders

## Conversation Design Principles

1. **Natural**: Uses conversational language rather than formal medical questionnaires
2. **Efficient**: Collects information in a logical order with minimal repetition
3. **Empathetic**: Shows understanding when discussing medical concerns
4. **Resilient**: Handles unexpected inputs and recovers from errors gracefully
5. **Flexible**: Adapts to the patient's communication style and information provision order

## Technical Requirements

- Python 3.8+
- LiveKit for voice orchestration
- SQLite database (configurable to other SQL databases)
- Asyncio for non-blocking operations 