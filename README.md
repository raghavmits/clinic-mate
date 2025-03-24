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
#Update the .env file with your own credentials
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Create the sample data (specialties, doctors and availabilities)
python scripts/create_sample_data.py

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

## Code Structure

The Clinic-Mate system is organized into the following modular components:

```
clinic-mate/
├── agent.py             # Main voice agent entry point and event handling
├── api.py               # Function context and patient registration functions
├── call_processor.py    # Call termination and summary processing
├── database.py          # Database models and operations
├── prompts.py           # System prompts for the LLM
├── requirements.txt     # Project dependencies
├── utils/               # Utility modules
│   ├── __init__.py      # Package exports
│   ├── appointment_utils.py  # Appointment-related utilities
│   ├── date_utils.py    # Date and time parsing utilities
│   ├── email_utils.py   # Email generation and sending
│   ├── extraction_utils.py  # Data extraction from conversations
│   └── summary_utils.py # Summary generation utilities
└── scripts/             # Utility scripts for setup and testing
    └── create_sample_data.py # Creates sample data for testing
    └── create_inbound_trunk.py # Creates an inbound trunk for testing
```

### Core Components

- **agent.py**: The main entry point that handles the voice processing pipeline, user interaction, and coordinates the system components
- **api.py**: Contains the `ClinicMateFunctions` class with AI callable functions for patient registration and appointment booking
- **call_processor.py**: Handles end-of-call operations like data persistence and summary generation
- **database.py**: Contains SQLModel database models and functions for data management

### Utility Modules

The system has been designed with modularity in mind, with specialized utility modules:

- **date_utils.py**: Handles date and time parsing with multiple format support
- **email_utils.py**: Provides functionality for creating and sending email confirmations
- **summary_utils.py**: Contains functions for generating formatted summaries
- **extraction_utils.py**: Provides regex-based extraction of patient information from conversations
- **appointment_utils.py**: Handles appointment-specific operations and formatting
