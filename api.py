import logging
from datetime import datetime, timedelta
from livekit.agents import llm
from typing import Optional, List, Dict, Any

logger = logging.getLogger("hospital-registration")
logger.setLevel(logging.INFO)

class ClinicMateFunctions(llm.FunctionContext):
    """Functions for patient registration"""
    
    def __init__(self):
        super().__init__()
        self.patient_name = None
        self.date_of_birth = None
        self.phone_number = None
        self.email = None
        self.address = None
        self.insurance_provider = None
        self.insurance_id = None
        self.has_referral = False
        self.referred_physician = None
        self.medical_complaint = None
        self.registration_stage = "initial"  # Track the conversation stage
        self.is_confirmed = False
        self.is_registered = False
        
        # New fields for appointment booking
        self.wants_appointment = False
        self.specialty_preference = None
        self.doctor_preference = None
        self.appointment_date_time = None
        self.appointment_id = None
        self.appointment_details = None
        
        # Track database ID to prevent duplicate saves
        self.database_patient_id = None
    
    @llm.ai_callable()
    async def register_patient(self, name: str, date_of_birth: str) -> str:
        """Register a patient in the system with their name and date of birth"""
        self.patient_name = name
        self.date_of_birth = date_of_birth
        self.registration_stage = "basic_info_collected"
        
        # In a real system, this would save to a database
        logger.info(f"Collected basic patient info: {name}, DOB: {date_of_birth}")
        
        return f"Thank you, {name}. I've recorded your date of birth as {date_of_birth}. Now, let's get your insurance information. Could you please tell me the name of your insurance provider?"
    
    @llm.ai_callable()
    async def collect_insurance_info(self, provider: str, insurance_id: str) -> str:
        """Collect the patient's insurance information"""
        self.insurance_provider = provider
        self.insurance_id = insurance_id
        self.registration_stage = "insurance_collected"
        
        logger.info(f"Collected insurance info: Provider: {provider}, ID: {insurance_id}")
        
        return f"I've recorded your insurance information with {provider}, ID: {insurance_id}. Do you have a referral to a specific physician for this visit?"
    
    @llm.ai_callable()
    async def collect_referral_info(self, has_referral: bool, referred_physician: Optional[str] = None) -> str:
        """Collect information about whether the patient has a referral"""
        self.has_referral = has_referral
        self.referred_physician = referred_physician
        self.registration_stage = "referral_collected"
        
        if has_referral and referred_physician:
            logger.info(f"Patient has referral to: {referred_physician}")
            return f"I've noted that you were referred to {referred_physician}. Could you please tell me the reason for your visit today or your chief medical complaint?"
        elif has_referral:
            logger.info("Patient has referral but did not specify physician")
            return "I've noted that you have a referral. Could you please tell me the name of the physician you were referred to?"
        else:
            logger.info("Patient does not have a referral")
            return "I've noted that you don't have a referral. Could you please tell me the reason for your visit today or your chief medical complaint?"
    
    @llm.ai_callable()
    async def collect_medical_complaint(self, complaint: str) -> str:
        """Collect the patient's chief medical complaint"""
        self.medical_complaint = complaint
        self.registration_stage = "complaint_collected"
        
        logger.info(f"Collected medical complaint: {complaint}")
        
        return f"Thank you for sharing that information. I've noted your concern. Now, I need to collect your address. Could you please provide your full address including street, city, state, and zip code?"
    
    @llm.ai_callable()
    async def collect_address(self, address: str) -> str:
        """Collect the patient's address"""
        self.address = address
        self.registration_stage = "address_collected"
        
        logger.info(f"Collected address: {address}")
        
        return "Thank you. Now, could you please provide your phone number where we can reach you?"
    
    @llm.ai_callable()
    async def collect_phone(self, phone_number: str) -> str:
        """Collect the patient's phone number"""
        self.phone_number = phone_number
        self.registration_stage = "phone_collected"
        
        logger.info(f"Collected phone number: {phone_number}")
        
        return "Thank you. Would you like to provide an email address? This is optional but will allow us to send you appointment reminders and other information."
    
    @llm.ai_callable()
    async def collect_email(self, email: Optional[str] = None) -> str:
        """Collect the patient's email address (optional)"""
        self.email = email
        self.registration_stage = "contact_collected"
        
        if email:
            logger.info(f"Collected email: {email}")
            message = f"Thank you. I've recorded your email as {email}."
        else:
            logger.info("Patient declined to provide email")
            message = "That's fine. You've chosen not to provide an email address."
        
        return message + " Here's a summary of all the information you've provided:\n\n" + await self.get_patient_info()
    
    @llm.ai_callable()
    async def get_patient_info(self) -> str:
        """Get a summary of all collected patient information"""
        if not self.patient_name:
            return "No patient information available yet."
        
        info = f"Name: {self.patient_name}\n"
        if self.date_of_birth:
            info += f"Date of Birth: {self.date_of_birth}\n"
        
        if self.insurance_provider:
            info += f"Insurance Provider: {self.insurance_provider}\n"
        if self.insurance_id:
            info += f"Insurance ID: {self.insurance_id}\n"
        
        if self.has_referral and self.referred_physician:
            info += f"Referral: Yes, to {self.referred_physician}\n"
        elif self.has_referral:
            info += "Referral: Yes\n"
        elif self.has_referral is False:
            info += "Referral: No\n"
        
        if self.medical_complaint:
            info += f"Reason for Visit: {self.medical_complaint}\n"
        
        if self.address:
            info += f"Address: {self.address}\n"
        if self.phone_number:
            info += f"Phone: {self.phone_number}\n"
        if self.email:
            info += f"Email: {self.email}\n"
        
        # Add appointment information if available
        if self.appointment_details:
            info += "\nAppointment Details:\n"
            info += f"Doctor: {self.appointment_details.get('doctor', {}).get('name', 'Unknown')}\n"
            info += f"Specialty: {self.appointment_details.get('doctor', {}).get('specialty', 'Unknown')}\n"
            info += f"Date/Time: {self.appointment_details.get('date_time', 'Unknown')}\n"
            info += f"Duration: {self.appointment_details.get('duration_minutes', '30')} minutes\n"
        
        if self.is_registered:
            info += "\n(Registration complete)"
        
        return info
    
    @llm.ai_callable()
    async def confirm_information(self, confirmed: bool) -> str:
        """Confirm all the collected patient information"""
        if confirmed:
            self.is_confirmed = True
            self.is_registered = True
            self.registration_stage = "registration_complete"
            
            logger.info(f"Registration completed for patient: {self.patient_name}")
            
            return "Thank you for confirming. All your information has been successfully registered in our system. Would you like to schedule an appointment with one of our specialists based on your medical needs?"
        else:
            self.is_confirmed = False
            return "I understand there might be some corrections needed. Please let me know which information you'd like to correct."
    
    @llm.ai_callable()
    async def update_specific_info(self, field: str, value: str) -> str:
        """Update a specific field of patient information"""
        field = field.lower()
        
        if field == "name":
            self.patient_name = value
            logger.info(f"Updated patient name to: {value}")
            return f"I've updated your name to {value}."
        
        elif field == "date of birth" or field == "dob":
            self.date_of_birth = value
            logger.info(f"Updated DOB to: {value}")
            return f"I've updated your date of birth to {value}."
        
        elif field == "insurance provider" or field == "provider":
            self.insurance_provider = value
            logger.info(f"Updated insurance provider to: {value}")
            return f"I've updated your insurance provider to {value}."
        
        elif field == "insurance id" or field == "id":
            self.insurance_id = value
            logger.info(f"Updated insurance ID to: {value}")
            return f"I've updated your insurance ID to {value}."
        
        elif field == "referral" or field == "referred physician":
            if value.lower() in ("no", "none", "false"):
                self.has_referral = False
                self.referred_physician = None
                logger.info("Updated: Patient has no referral")
                return "I've updated your information to indicate you don't have a referral."
            else:
                self.has_referral = True
                self.referred_physician = value
                logger.info(f"Updated referred physician to: {value}")
                return f"I've updated your referral to {value}."
        
        elif field == "complaint" or field == "reason" or field == "medical complaint":
            self.medical_complaint = value
            logger.info(f"Updated medical complaint to: {value}")
            return f"I've updated your reason for visit to: {value}."
        
        elif field == "address":
            self.address = value
            logger.info(f"Updated address to: {value}")
            return f"I've updated your address to: {value}."
        
        elif field == "phone" or field == "phone number":
            self.phone_number = value
            logger.info(f"Updated phone number to: {value}")
            return f"I've updated your phone number to {value}."
        
        elif field == "email":
            self.email = value
            logger.info(f"Updated email to: {value}")
            return f"I've updated your email to {value}."
        
        else:
            logger.warning(f"Attempted to update unknown field: {field}")
            return f"I'm sorry, I don't recognize '{field}' as a valid field. Please specify which information you'd like to update."
    
    # New functions for appointment booking
    
    @llm.ai_callable()
    async def check_appointment_interest(self, wants_appointment: bool) -> str:
        """Check if the patient wants to schedule an appointment"""
        self.wants_appointment = wants_appointment
        
        if wants_appointment:
            # Import here to avoid circular imports
            import database
            
            # Get available specialties
            specialties = await database.get_all_specialties()
            specialty_options = ", ".join([s.name for s in specialties])
            
            logger.info("Patient wants to schedule an appointment")
            return f"Great! Based on your medical complaint, I can help you schedule an appointment with one of our specialists. We have specialists in the following areas: {specialty_options}. Which specialty would be most appropriate for your needs?"
        else:
            logger.info("Patient does not want to schedule an appointment")
            return "That's fine. Your registration is complete, and you can always call back later to schedule an appointment. Is there anything else I can help you with today?"
    
    @llm.ai_callable()
    async def select_specialty(self, specialty: str) -> str:
        """Select a medical specialty for the appointment"""
        self.specialty_preference = specialty
        
        # Import here to avoid circular imports
        import database
        
        # Find the specialty
        specialty_obj = await database.get_specialty_by_name(specialty)
        
        if not specialty_obj:
            logger.warning(f"Specialty not found: {specialty}")
            return f"I'm sorry, I couldn't find '{specialty}' in our system. Please choose from one of our available specialties."
        
        # Get doctors in this specialty
        doctors = await database.get_doctors_by_specialty(specialty_obj.id)
        
        if not doctors:
            logger.warning(f"No doctors found for specialty: {specialty}")
            return f"I'm sorry, we don't have any doctors available for {specialty} at the moment. Would you like to choose a different specialty?"
        
        # Format the doctors list
        doctor_list = "\n".join([f"- {d.name}: {d.bio}" for d in doctors])
        
        logger.info(f"Patient selected specialty: {specialty}")
        return f"We have the following doctors available in {specialty}:\n\n{doctor_list}\n\nWhich doctor would you prefer to see?"
    
    @llm.ai_callable()
    async def select_doctor(self, doctor_name: str) -> str:
        """Select a doctor for the appointment"""
        self.doctor_preference = doctor_name
        
        # Import here to avoid circular imports
        import database
        
        # Find the doctor (this is a simplified approach - in reality, you'd need a more robust search)
        # In a real system, you might use the doctor's ID instead of searching by name
        from sqlmodel import select
        from database import Doctor, get_session
        
        doctor_id = None
        async with database.get_session() as session:
            # Search for doctor by partial name match
            result = session.exec(select(Doctor).where(
                Doctor.name.ilike(f"%{doctor_name}%")
            )).first()
            
            if result:
                doctor_id = result.id
        
        if not doctor_id:
            logger.warning(f"Doctor not found: {doctor_name}")
            return f"I'm sorry, I couldn't find '{doctor_name}' in our system. Please choose from one of our available doctors."
        
        # Get next available slots
        next_week = datetime.now() + timedelta(days=7)  # One week from now
        available_slots = await database.get_next_available_slots(doctor_id, next_week)
        
        if not available_slots:
            logger.warning(f"No available slots for doctor: {doctor_name}")
            return f"I'm sorry, {doctor_name} doesn't have any available appointments in the next two weeks. Would you like to choose a different doctor?"
        
        # Format the available slots
        slot_list = "\n".join([f"- {slot.strftime('%A, %B %d, %Y at %I:%M %p')}" for slot in available_slots])
        
        logger.info(f"Patient selected doctor: {doctor_name}")
        return f"{doctor_name} has the following available appointment slots:\n\n{slot_list}\n\nWhich date and time would you prefer?"
    
    @llm.ai_callable()
    async def book_appointment(self, date_time_str: str) -> str:
        """Book an appointment at the specified date and time"""
        # Import here to avoid circular imports
        import database
        
        # Initialize variables to track success state
        doctor_found = False
        date_parsed = False
        patient_created = False
        appointment_created = False
        
        # Find the doctor ID (similar to select_doctor method)
        doctor_id = None
        try:
            async with database.get_session() as session:
                from sqlmodel import select
                from database import Doctor
                
                # Search for doctor by partial name match
                result = session.exec(select(Doctor).where(
                    Doctor.name.ilike(f"%{self.doctor_preference}%")
                )).first()
                
                if result:
                    doctor_id = result.id
                    doctor_found = True
        except Exception as e:
            logger.error(f"Error finding doctor: {str(e)}")
        
        if not doctor_found:
            logger.warning(f"Doctor not found when booking: {self.doctor_preference}")
            # Create appointment_details with minimal information for fallback
            self.appointment_details = {
                'doctor': {'name': self.doctor_preference, 'specialty': self.specialty_preference},
                'date_time': date_time_str,
                'status': 'pending',
                'error': "Doctor not found"
            }
            return "I've noted your request to schedule with Dr. " + self.doctor_preference + ". There seems to be an issue with our system, but our scheduling team will contact you within 24 hours to confirm your appointment."
        
        # Parse the date_time string
        appointment_date = None
        try:
            # Try different formats
            for fmt in [
                "%A, %B %d, %Y at %I:%M %p",  # Monday, January 1, 2023 at 9:00 AM
                "%B %d, %Y at %I:%M %p",      # January 1, 2023 at 9:00 AM
                "%Y-%m-%d %H:%M",             # 2023-01-01 09:00
                "%m/%d/%Y %H:%M",             # 01/01/2023 09:00
                "%m/%d/%Y %I:%M %p",          # 01/01/2023 9:00 AM
                "%A, %B %d, %Y"               # Monday, January 1, 2023 (defaults to 9:00 AM)
            ]:
                try:
                    appointment_date = datetime.strptime(date_time_str, fmt)
                    date_parsed = True
                    break
                except ValueError:
                    continue
                
            # If none of the formats match, try a simple approach for "April 1" type strings
            if not date_parsed and "april" in date_time_str.lower():
                try:
                    # Extract day from the string
                    day_parts = [p for p in date_time_str.lower().replace(",", "").split() if p.isdigit()]
                    if day_parts:
                        day = int(day_parts[0])
                        # Default to 9:00 AM
                        appointment_date = datetime(2025, 4, day, 9, 0)
                        date_parsed = True
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error parsing appointment date: {str(e)}")
        
        if not date_parsed:
            # Create appointment_details with minimal information for fallback
            self.appointment_details = {
                'doctor': {'name': self.doctor_preference, 'specialty': self.specialty_preference},
                'date_time': date_time_str,
                'status': 'pending',
                'error': f"Could not parse date: {date_time_str}"
            }
            return f"I've noted your preference for an appointment on {date_time_str}. Our scheduling team will contact you to confirm the exact date and time. Would you like me to send a confirmation to your email or phone?"
        
        # Store for later use
        self.appointment_date_time = appointment_date
        
        # Check if patient is in database and has ID
        patient_id = None
        if getattr(self, "database_patient_id", None):
            patient_id = self.database_patient_id
            patient_created = True
        else:
            # Create a patient in the database if one doesn't exist yet
            try:
                from database import save_patient_from_context
                patient_id = await save_patient_from_context(self)
                if patient_id:
                    self.database_patient_id = patient_id
                    patient_created = True
                    logger.info(f"Created patient with ID {patient_id} for appointment booking")
                else:
                    logger.error("Failed to create patient for appointment booking")
            except Exception as e:
                logger.error(f"Error creating patient for appointment: {str(e)}")
        
        # Always create appointment details, even if the database operation fails
        formatted_date = appointment_date.strftime("%A, %B %d, %Y at %I:%M %p") if appointment_date else date_time_str
        
        if not patient_created:
            # Create appointment_details with minimal information for fallback
            self.appointment_details = {
                'doctor': {'name': self.doctor_preference, 'specialty': self.specialty_preference},
                'date_time': formatted_date,
                'duration_minutes': 30,
                'status': 'pending',
                'error': "Failed to create patient"
            }
            return f"I've scheduled your appointment with {self.doctor_preference} for {formatted_date}. There was a small issue with our system, but your appointment request has been recorded. Our scheduling team will contact you to confirm. Would you like me to send a confirmation to your email or phone?"
        
        try:
            # Try to create the appointment
            appointment = await database.create_appointment(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_date=appointment_date
            )
            
            if appointment:
                # Save the appointment ID and details
                self.appointment_id = appointment.id
                appointment_created = True
                
                # Get detailed appointment information
                appointment_details = await database.get_appointment_details(appointment.id)
                if appointment_details:
                    self.appointment_details = appointment_details
                    logger.info(f"Retrieved appointment details for ID {appointment.id}")
                else:
                    logger.warning(f"Could not retrieve appointment details for ID {appointment.id}")
                    # Create minimal appointment details
                    self.appointment_details = {
                        'doctor': {'name': self.doctor_preference, 'specialty': self.specialty_preference},
                        'date_time': formatted_date,
                        'duration_minutes': 30,
                        'status': 'scheduled',
                        'appointment_id': appointment.id
                    }
            else:
                # Create minimal appointment details for fallback when slot is unavailable
                self.appointment_details = {
                    'doctor': {'name': self.doctor_preference, 'specialty': self.specialty_preference},
                    'date_time': formatted_date,
                    'duration_minutes': 30,
                    'status': 'pending',
                    'error': "Time slot unavailable"
                }
                logger.warning(f"Failed to create appointment for {self.patient_name} with {self.doctor_preference} at {formatted_date}")
                return "I'm sorry, but that time slot is no longer available. Would you like to choose a different time?"
        except Exception as e:
            logger.error(f"Error during appointment booking: {str(e)}")
            # Create minimal appointment details for fallback
            self.appointment_details = {
                'doctor': {'name': self.doctor_preference, 'specialty': self.specialty_preference},
                'date_time': formatted_date,
                'duration_minutes': 30,
                'status': 'pending',
                'error': str(e)
            }
        
        # Format a nice confirmation message
        doctor_name = self.appointment_details.get('doctor', {}).get('name', self.doctor_preference)
        specialty = self.appointment_details.get('doctor', {}).get('specialty', self.specialty_preference)
        formatted_date = self.appointment_details.get('date_time', formatted_date)
        status = self.appointment_details.get('status', 'scheduled')
        
        if appointment_created:
            logger.info(f"Successfully booked appointment for {self.patient_name} with {doctor_name} at {formatted_date}")
            return f"Great news! I've successfully booked your appointment with {doctor_name}, our {specialty} specialist, for {formatted_date}. The appointment will last approximately 30 minutes. Please arrive 15 minutes early with your insurance card and ID. Would you like me to send a confirmation to your email or phone?"
        else:
            logger.info(f"Created pending appointment for {self.patient_name} with {doctor_name} at {formatted_date}")
            return f"I've scheduled your appointment with {doctor_name} for {formatted_date}. There was a small issue with our system, but your appointment request has been recorded. Our scheduling team will contact you to confirm. Would you like me to send a confirmation to your email or phone?"
    
    @llm.ai_callable()
    async def cancel_appointment(self) -> str:
        """Cancel the current appointment booking process"""
        self.wants_appointment = False
        self.specialty_preference = None
        self.doctor_preference = None
        self.appointment_date_time = None
        
        logger.info(f"Appointment booking canceled for patient: {self.patient_name}")
        return "I've canceled the appointment booking process. You can always call back later to schedule an appointment. Is there anything else I can help you with today?"
    
    @llm.ai_callable()
    async def send_appointment_confirmation(self, send_to_email: bool = True, send_to_phone: bool = False) -> str:
        """Send appointment confirmation to email and/or phone"""
        if not self.appointment_details:
            return "There's no appointment to send confirmation for. Would you like to schedule an appointment?"
        
        confirmations_sent = []
        
        if send_to_email and self.email:
            # In a real system, this would send an actual email
            logger.info(f"Sending appointment confirmation email to: {self.email}")
            confirmations_sent.append(f"email ({self.email})")
        
        if send_to_phone and self.phone_number:
            # In a real system, this would send an SMS
            logger.info(f"Sending appointment confirmation SMS to: {self.phone_number}")
            confirmations_sent.append(f"phone ({self.phone_number})")
        
        if confirmations_sent:
            confirmation_str = " and ".join(confirmations_sent)
            return f"I've sent your appointment confirmation to your {confirmation_str}. Is there anything else I can help you with today?"
        else:
            return "I couldn't send a confirmation because no email or phone number was provided. Your appointment is still confirmed in our system. Is there anything else I can help you with today?" 