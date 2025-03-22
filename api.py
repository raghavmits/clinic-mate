import logging
from datetime import datetime
from livekit.agents import llm

logger = logging.getLogger("hospital-registration")
logger.setLevel(logging.INFO)

class ClinicMateFunctions(llm.FunctionContext):
    """Functions for patient registration"""
    
    def __init__(self):
        super().__init__()
        self.patient_name = None
        self.date_of_birth = None
        self.is_confirmed = False
        self.is_registered = False
    
    @llm.ai_callable()
    async def register_patient(self, name: str, date_of_birth: str) -> str:
        """Register a patient in the system with their name and date of birth"""
        self.patient_name = name
        self.date_of_birth = date_of_birth
        self.is_registered = True
        
        # In a real system, this would save to a database
        logger.info(f"Registered patient: {name}, DOB: {date_of_birth}")
        
        return f"Patient {name} with date of birth {date_of_birth} has been successfully registered."
    
    @llm.ai_callable()
    async def get_patient_info(self) -> str:
        """Get the current patient information"""
        if not self.patient_name:
            return "No patient information available yet."
        
        info = f"Name: {self.patient_name}"
        if self.date_of_birth:
            info += f", Date of Birth: {self.date_of_birth}"
        if self.is_registered:
            info += " (Registered)"
        
        return info
    
    @llm.ai_callable()
    async def confirm_information(self, confirmed: bool) -> str:
        """Confirm the patient information"""
        if confirmed:
            self.is_confirmed = True
            return "Information confirmed."
        else:
            # Reset information if not confirmed
            self.patient_name = None
            self.date_of_birth = None
            self.is_confirmed = False
            return "Information reset. Let's start over." 