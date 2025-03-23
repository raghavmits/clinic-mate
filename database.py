"""
Database models and functions for the patient registration system.
Uses SQLModel (SQLAlchemy + Pydantic) for type-safe database interactions.
"""

import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sqlmodel import Field, SQLModel, Session, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm.session import make_transient_to_detached
from contextlib import asynccontextmanager
import asyncio

# Import ClinicMateFunctions for proper type hints
from api import ClinicMateFunctions

# Create a logger
logger = logging.getLogger("database")
logger.setLevel(logging.INFO)

# Assuming SQLite for simplicity - can be changed to PostgreSQL, MySQL, etc.
DATABASE_URL = "sqlite:///./clinic_mate.db"

# Create async engine for SQLModel
engine = create_engine(DATABASE_URL, echo=False)

# Models

class PatientBase(SQLModel):
    """Base model for patient information shared by all patient-related schemas"""
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    has_referral: bool = False
    referred_physician: Optional[str] = None
    medical_complaint: Optional[str] = None


class Patient(PatientBase, table=True):
    """SQLModel database model for patients"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PatientCreate(PatientBase):
    """Schema for creating a new patient"""
    pass


class PatientRead(PatientBase):
    """Schema for reading patient data"""
    id: int
    created_at: datetime
    updated_at: datetime


class PatientUpdate(SQLModel):
    """Schema for updating patient data - all fields optional"""
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    has_referral: Optional[bool] = None
    referred_physician: Optional[str] = None
    medical_complaint: Optional[str] = None


# Database Functions

def create_db_and_tables():
    """Create the database and tables if they don't exist"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database and tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database and tables: {str(e)}")
        raise


@asynccontextmanager
async def get_session():
    """Get a database session - async context manager"""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


async def add_patient(patient_data: PatientCreate) -> PatientRead:
    """
    Add a new patient to the database
    
    Args:
        patient_data: The patient data to add
        
    Returns:
        The created patient with ID
    """
    async with get_session() as session:
        db_patient = Patient.from_orm(patient_data)
        session.add(db_patient)
        session.commit()
        session.refresh(db_patient)
        
        # Convert to PatientRead
        patient_read = PatientRead.from_orm(db_patient)
        make_transient_to_detached(patient_read)
        return patient_read


async def get_patient(patient_id: int) -> Optional[PatientRead]:
    """
    Get a patient by ID
    
    Args:
        patient_id: The ID of the patient to get
        
    Returns:
        The patient if found, None otherwise
    """
    async with get_session() as session:
        patient = session.get(Patient, patient_id)
        if not patient:
            return None
            
        # Convert to PatientRead
        patient_read = PatientRead.from_orm(patient)
        make_transient_to_detached(patient_read)
        return patient_read


async def update_patient(patient_id: int, patient_data: PatientUpdate) -> Optional[PatientRead]:
    """
    Update an existing patient
    
    Args:
        patient_id: The ID of the patient to update
        patient_data: The patient data to update
        
    Returns:
        The updated patient if found, None otherwise
    """
    async with get_session() as session:
        patient = session.get(Patient, patient_id)
        if not patient:
            return None
            
        # Update fields that are not None
        patient_dict = patient_data.dict(exclude_unset=True)
        for key, value in patient_dict.items():
            if value is not None:
                setattr(patient, key, value)
                
        # Update the updated_at timestamp
        patient.updated_at = datetime.now()
        
        session.add(patient)
        session.commit()
        session.refresh(patient)
        
        # Convert to PatientRead
        patient_read = PatientRead.from_orm(patient)
        make_transient_to_detached(patient_read)
        return patient_read


async def update_insurance_info(
    patient_id: int,
    provider: str,
    insurance_id: str,
    has_referral: bool = False,
    referred_physician: Optional[str] = None
) -> bool:
    """
    Update insurance information for a patient
    
    Args:
        patient_id: The ID of the patient
        provider: The insurance provider
        insurance_id: The insurance ID
        has_referral: Whether the patient has a referral
        referred_physician: The name of the physician the patient was referred to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create update data
        update_data = PatientUpdate(
            insurance_provider=provider,
            insurance_id=insurance_id,
            has_referral=has_referral,
            referred_physician=referred_physician
        )
        
        # Update the patient
        result = await update_patient(patient_id, update_data)
        return result is not None
    except Exception as e:
        logger.error(f"Error updating insurance info: {str(e)}")
        return False


async def update_medical_complaint(
    patient_id: int,
    complaint: str
) -> bool:
    """
    Update medical complaint for a patient
    
    Args:
        patient_id: The ID of the patient
        complaint: The patient's medical complaint
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create update data
        update_data = PatientUpdate(medical_complaint=complaint)
        
        # Update the patient
        result = await update_patient(patient_id, update_data)
        return result is not None
    except Exception as e:
        logger.error(f"Error updating medical complaint: {str(e)}")
        return False


async def get_full_patient_data(patient_id: int) -> Dict[str, Any]:
    """
    Get full patient data
    
    Args:
        patient_id: The ID of the patient
        
    Returns:
        Dictionary with patient data
    """
    result = {}
    
    async with get_session() as session:
        # Get patient
        patient = session.get(Patient, patient_id)
        if not patient:
            return {}
            
        # Convert to dict
        result = {
            "id": patient.id,
            "name": patient.name,
            "date_of_birth": patient.date_of_birth.isoformat(),
            "email": patient.email,
            "phone": patient.phone,
            "address": patient.address,
            "insurance_provider": patient.insurance_provider,
            "insurance_id": patient.insurance_id,
            "has_referral": patient.has_referral,
            "referred_physician": patient.referred_physician,
            "medical_complaint": patient.medical_complaint,
            "created_at": patient.created_at.isoformat(),
            "updated_at": patient.updated_at.isoformat()
        }
    
    return result 


# Functions moved from agent.py to improve modularity

async def save_patient_from_context(fnc_ctx: ClinicMateFunctions) -> int:
    """
    Save patient information from function context to the database
    
    Args:
        fnc_ctx: The ClinicMateFunctions context with patient information
            
    Returns:
        The patient ID if successful, None otherwise
    """
    # Convert date of birth string to date object
    try:
        # Try to parse the date of birth in common formats
        dob_str = fnc_ctx.date_of_birth
        try:
            # MM/DD/YYYY format
            dob = datetime.strptime(dob_str, '%m/%d/%Y').date()
        except ValueError:
            try:
                # YYYY-MM-DD format
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                # Try descriptive format (e.g., "January 15, 1980")
                dob = datetime.strptime(dob_str, '%B %d, %Y').date()
    except Exception as e:
        logger.error(f"Could not parse date of birth: {dob_str}, error: {str(e)}")
        # Use a placeholder date for demonstration (should handle more gracefully in production)
        dob = datetime.now().date()
    
    # Create new patient - simplified approach without checking for duplicates
    try:
        new_patient = PatientCreate(
            name=fnc_ctx.patient_name,
            date_of_birth=dob,
            email=fnc_ctx.email,
            phone=fnc_ctx.phone_number,
            address=fnc_ctx.address,
            insurance_provider=fnc_ctx.insurance_provider,
            insurance_id=fnc_ctx.insurance_id,
            has_referral=fnc_ctx.has_referral,
            referred_physician=fnc_ctx.referred_physician,
            medical_complaint=fnc_ctx.medical_complaint
        )
        
        patient = await add_patient(new_patient)
        patient_id = patient.id
        logger.info(f"Created new patient with ID: {patient_id}")
        return patient_id
    except Exception as e:
        logger.error(f"Error creating patient: {str(e)}")
        return None

async def update_patient_from_context(patient_id: int, fnc_ctx: ClinicMateFunctions, updated_field: str) -> bool:
    """
    Update specific fields of an existing patient record based on newly collected information
    
    Args:
        patient_id: The ID of the patient to update
        fnc_ctx: The ClinicMateFunctions context with patient information
        updated_field: The name of the function that was called to update information
            
    Returns:
        True if successful, False otherwise
    """
    try:
        # Handle different types of updates based on the function that was called
        if updated_field == "collect_insurance_info" and fnc_ctx.insurance_provider and fnc_ctx.insurance_id:
            # Update insurance information
            insurance_success = await update_insurance_info(
                patient_id=patient_id,
                provider=fnc_ctx.insurance_provider,
                insurance_id=fnc_ctx.insurance_id,
                has_referral=fnc_ctx.has_referral,
                referred_physician=fnc_ctx.referred_physician
            )
            
            if insurance_success:
                logger.info(f"Updated insurance information for patient: {patient_id}")
                return True
        
        elif updated_field == "collect_medical_complaint" and fnc_ctx.medical_complaint:
            # Update medical complaint
            medical_success = await update_medical_complaint(
                patient_id=patient_id,
                complaint=fnc_ctx.medical_complaint
            )
            
            if medical_success:
                logger.info(f"Updated medical record for patient: {patient_id}")
                return True
        
        elif updated_field in ("collect_address", "collect_phone", "collect_email"):
            # Update contact information
            update_data = PatientUpdate(
                email=fnc_ctx.email,
                phone=fnc_ctx.phone_number,
                address=fnc_ctx.address
            )
            
            updated_patient = await update_patient(patient_id, update_data)
            if updated_patient:
                logger.info(f"Updated contact information for patient: {patient_id}")
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error updating patient record: {str(e)}")
        return False 