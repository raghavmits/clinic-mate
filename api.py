import logging
from datetime import datetime
from livekit.agents import llm
from typing import Optional

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
            
            return "Thank you for confirming. All your information has been successfully registered in our system. You're all set for your appointment. Please arrive 15 minutes before your scheduled time. Is there anything else I can help you with today?"
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