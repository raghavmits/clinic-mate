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


# Doctor and Appointment Models

class SpecialtyBase(SQLModel):
    """Base model for medical specialties"""
    name: str
    description: Optional[str] = None


class Specialty(SpecialtyBase, table=True):
    """SQLModel database model for medical specialties"""
    id: Optional[int] = Field(default=None, primary_key=True)


class SpecialtyRead(SpecialtyBase):
    """Schema for reading specialty data"""
    id: int


class DoctorBase(SQLModel):
    """Base model for doctor information"""
    name: str
    specialty_id: int
    bio: Optional[str] = None


class Doctor(DoctorBase, table=True):
    """SQLModel database model for doctors"""
    id: Optional[int] = Field(default=None, primary_key=True)


class DoctorRead(DoctorBase):
    """Schema for reading doctor data"""
    id: int
    specialty: Optional[SpecialtyRead] = None


class AppointmentBase(SQLModel):
    """Base model for appointments"""
    patient_id: Optional[int] = None
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    status: str = "scheduled"  # scheduled, completed, canceled
    notes: Optional[str] = None


class Appointment(AppointmentBase, table=True):
    """SQLModel database model for appointments"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class AppointmentCreate(AppointmentBase):
    """Schema for creating a new appointment"""
    pass


class AppointmentRead(AppointmentBase):
    """Schema for reading appointment data"""
    id: int
    created_at: datetime
    patient: Optional[PatientRead] = None
    doctor: Optional[DoctorRead] = None


class DoctorAvailability(SQLModel, table=True):
    """SQLModel database model for doctor availabilities"""
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctor.id")
    date: date
    time: str   # Format: "HH:MM" in 24-hour format
    is_available: bool = True


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


async def add_patient(patient_data: PatientCreate) -> Optional[PatientRead]:
    """
    Add a new patient to the database
    
    Args:
        patient_data: Patient data to add
        
    Returns:
        Created patient with ID
    """
    async with get_session() as session:
        try:
            # Convert Pydantic model to SQLModel
            db_patient = Patient(
                name=patient_data.name,
                date_of_birth=patient_data.date_of_birth,
                email=patient_data.email,
                phone=patient_data.phone,
                address=patient_data.address,
                insurance_provider=patient_data.insurance_provider,
                insurance_id=patient_data.insurance_id,
                has_referral=patient_data.has_referral,
                referred_physician=patient_data.referred_physician,
                medical_complaint=patient_data.medical_complaint
            )
            
            session.add(db_patient)
            session.commit()
            session.refresh(db_patient)
            
            # Convert back to Pydantic model
            patient_read = PatientRead(
                id=db_patient.id,
                name=db_patient.name,
                date_of_birth=db_patient.date_of_birth,
                email=db_patient.email,
                phone=db_patient.phone,
                address=db_patient.address,
                insurance_provider=db_patient.insurance_provider,
                insurance_id=db_patient.insurance_id,
                has_referral=db_patient.has_referral,
                referred_physician=db_patient.referred_physician,
                medical_complaint=db_patient.medical_complaint,
                created_at=db_patient.created_at,
                updated_at=db_patient.updated_at
            )
            return patient_read
        except Exception as e:
            logger.error(f"Error adding patient: {str(e)}")
            return None


async def get_patient(patient_id: int) -> Optional[PatientRead]:
    """
    Get a patient by ID
    
    Args:
        patient_id: The ID of the patient to get
        
    Returns:
        Patient data, or None if not found
    """
    async with get_session() as session:
        try:
            patient = session.get(Patient, patient_id)
            if not patient:
                return None
                
            patient_read = PatientRead(
                id=patient.id,
                name=patient.name,
                date_of_birth=patient.date_of_birth,
                email=patient.email,
                phone=patient.phone,
                address=patient.address,
                insurance_provider=patient.insurance_provider,
                insurance_id=patient.insurance_id,
                has_referral=patient.has_referral,
                referred_physician=patient.referred_physician,
                medical_complaint=patient.medical_complaint,
                created_at=patient.created_at,
                updated_at=patient.updated_at
            )
            return patient_read
        except Exception as e:
            logger.error(f"Error getting patient: {str(e)}")
            return None


async def update_patient(patient_id: int, update_data: PatientUpdate) -> Optional[PatientRead]:
    """
    Update a patient
    
    Args:
        patient_id: The ID of the patient to update
        update_data: The data to update
        
    Returns:
        Updated patient data, or None if not found
    """
    async with get_session() as session:
        try:
            patient = session.get(Patient, patient_id)
            if not patient:
                return None
                
            # Apply updates - only set fields that are not None
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(patient, field, value)
                
            # Update the updated_at timestamp
            patient.updated_at = datetime.now()
            
            session.add(patient)
            session.commit()
            session.refresh(patient)
            
            patient_read = PatientRead(
                id=patient.id,
                name=patient.name,
                date_of_birth=patient.date_of_birth,
                email=patient.email,
                phone=patient.phone,
                address=patient.address,
                insurance_provider=patient.insurance_provider,
                insurance_id=patient.insurance_id,
                has_referral=patient.has_referral,
                referred_physician=patient.referred_physician,
                medical_complaint=patient.medical_complaint,
                created_at=patient.created_at,
                updated_at=patient.updated_at
            )
            return patient_read
        except Exception as e:
            logger.error(f"Error updating patient: {str(e)}")
            return None


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
                try:
                    # Try descriptive format (e.g., "January 15, 1980")
                    dob = datetime.strptime(dob_str, '%B %d, %Y').date()
                except ValueError:
                    # Try additional formats
                    try:
                        # Try M/D/YYYY format
                        dob = datetime.strptime(dob_str, '%-m/%-d/%Y').date()
                    except ValueError:
                        # Try D-M-YYYY format
                        dob = datetime.strptime(dob_str, '%-d-%-m-%Y').date()
    except Exception as e:
        logger.error(f"Could not parse date of birth: {dob_str}, error: {str(e)}")
        # Use a placeholder date for demonstration (should handle more gracefully in production)
        dob = datetime.now().date()
    
    # Create new patient directly without using the PatientRead model
    try:
        async with get_session() as session:
            # Create a new Patient record directly 
            new_patient = Patient(
                name=fnc_ctx.patient_name,
                date_of_birth=dob,
                email=fnc_ctx.email,
                phone=fnc_ctx.phone_number,
                address=fnc_ctx.address,
                insurance_provider=fnc_ctx.insurance_provider,
                insurance_id=fnc_ctx.insurance_id,
                has_referral=fnc_ctx.has_referral,
                referred_physician=fnc_ctx.referred_physician,
                medical_complaint=fnc_ctx.medical_complaint,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add to session and commit
            session.add(new_patient)
            session.commit()
            session.refresh(new_patient)
            
            # Get the ID directly
            patient_id = new_patient.id
            
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

# Doctor and Appointment Functions

async def add_specialty(name: str, description: Optional[str] = None) -> Optional[SpecialtyRead]:
    """
    Add a new medical specialty
    
    Args:
        name: The name of the specialty
        description: Optional description of the specialty
        
    Returns:
        The created specialty with ID
    """
    async with get_session() as session:
        try:
            # First, check if the specialty already exists to avoid duplicates
            existing = session.exec(select(Specialty).where(Specialty.name == name)).first()
            if existing:
                logger.info(f"Specialty already exists: {name}")
                # Convert to SpecialtyRead without detaching
                return SpecialtyRead(id=existing.id, name=existing.name, description=existing.description)
            
            # Create new specialty
            specialty = Specialty(name=name, description=description)
            session.add(specialty)
            session.commit()
            session.refresh(specialty)
            
            # Convert to SpecialtyRead without using from_orm which causes the _sa_instance_state issue
            return SpecialtyRead(id=specialty.id, name=specialty.name, description=specialty.description)
        except Exception as e:
            logger.error(f"Error adding specialty: {str(e)}")
            return None


async def add_doctor(
    name: str, 
    specialty_id: int,
    bio: Optional[str] = None
) -> Optional[DoctorRead]:
    """
    Add a new doctor
    
    Args:
        name: The name of the doctor
        specialty_id: The ID of the doctor's specialty
        bio: Optional bio for the doctor
        
    Returns:
        The created doctor with ID
    """
    async with get_session() as session:
        try:
            # First, check if the doctor already exists
            existing = session.exec(select(Doctor).where(Doctor.name == name)).first()
            if existing:
                logger.info(f"Doctor already exists: {name}")
                # Convert to DoctorRead without detaching
                return DoctorRead(id=existing.id, name=existing.name, specialty_id=existing.specialty_id, bio=existing.bio)
            
            # Create new doctor
            doctor = Doctor(
                name=name,
                specialty_id=specialty_id,
                bio=bio
            )
            session.add(doctor)
            session.commit()
            session.refresh(doctor)
            
            # Convert to DoctorRead without using from_orm
            return DoctorRead(id=doctor.id, name=doctor.name, specialty_id=doctor.specialty_id, bio=doctor.bio)
        except Exception as e:
            logger.error(f"Error adding doctor: {str(e)}")
            return None


async def add_doctor_availability(
    doctor_id: int,
    availability_date: date,
    availability_time: str,
    is_available: bool = True
) -> bool:
    """
    Add availability for a doctor
    
    Args:
        doctor_id: The ID of the doctor
        availability_date: The date the doctor is available
        availability_time: The time in "HH:MM" format (24-hour)
        is_available: Whether the doctor is available during this time
        
    Returns:
        True if successful, False otherwise
    """
    async with get_session() as session:
        try:
            availability = DoctorAvailability(
                doctor_id=doctor_id,
                date=availability_date,
                time=availability_time,
                is_available=is_available
            )
            session.add(availability)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding doctor availability: {str(e)}")
            return False


async def get_all_specialties() -> List[SpecialtyRead]:
    """
    Get all specialties
    
    Returns:
        List of all specialties
    """
    async with get_session() as session:
        try:
            result = session.exec(select(Specialty)).all()
            return [SpecialtyRead(id=s.id, name=s.name, description=s.description) for s in result]
        except Exception as e:
            logger.error(f"Error getting specialties: {str(e)}")
            return []


async def get_doctors_by_specialty(specialty_id: int) -> List[DoctorRead]:
    """
    Get all doctors for a given specialty
    
    Args:
        specialty_id: The ID of the specialty
        
    Returns:
        List of doctors in the specialty
    """
    async with get_session() as session:
        try:
            result = session.exec(select(Doctor).where(Doctor.specialty_id == specialty_id)).all()
            return [DoctorRead(id=d.id, name=d.name, specialty_id=d.specialty_id, bio=d.bio) for d in result]
        except Exception as e:
            logger.error(f"Error getting doctors by specialty: {str(e)}")
            return []


async def get_specialty_by_name(name: str) -> Optional[SpecialtyRead]:
    """
    Get a specialty by name
    
    Args:
        name: The name of the specialty (case-insensitive partial match)
        
    Returns:
        The specialty if found, None otherwise
    """
    async with get_session() as session:
        try:
            # Case-insensitive search with partial match
            result = session.exec(select(Specialty).where(
                Specialty.name.ilike(f"%{name}%")
            )).first()
            
            if result:
                specialty_read = SpecialtyRead(
                    id=result.id,
                    name=result.name,
                    description=result.description
                )
                return specialty_read
            return None
        except Exception as e:
            logger.error(f"Error getting specialty by name: {str(e)}")
            return None


async def get_doctor_availability(doctor_id: int, from_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """
    Get availability for a doctor
    
    Args:
        doctor_id: The ID of the doctor
        from_date: Optional date to filter availabilities from (inclusive)
        
    Returns:
        List of availability time slots
    """
    async with get_session() as session:
        try:
            # Start with the base query
            query = select(DoctorAvailability).where(
                DoctorAvailability.doctor_id == doctor_id
            ).where(
                DoctorAvailability.is_available == True
            )
            
            # Add date filter if provided
            if from_date:
                query = query.where(DoctorAvailability.date >= from_date)
                
            # Order by date and time
            query = query.order_by(DoctorAvailability.date, DoctorAvailability.time)
            
            # Execute the query
            result = session.exec(query).all()
            
            # Convert to a more usable format
            availability = []
            
            for slot in result:
                # Format the date
                date_formatted = slot.date.strftime("%A, %B %d, %Y")
                
                availability.append({
                    "date": date_formatted,
                    "date_obj": slot.date,
                    "time": slot.time,
                    "is_available": slot.is_available
                })
                
            return availability
        except Exception as e:
            logger.error(f"Error getting doctor availability: {str(e)}")
            return []


async def create_appointment(
    doctor_id: int,
    patient_id: int,
    appointment_date: datetime,
    duration_minutes: int = 30,
    notes: Optional[str] = None
) -> Optional[AppointmentRead]:
    """
    Create a new appointment
    
    Args:
        doctor_id: The ID of the doctor
        patient_id: The ID of the patient
        appointment_date: The date and time of the appointment
        duration_minutes: The duration of the appointment in minutes
        notes: Optional notes for the appointment
        
    Returns:
        The created appointment with ID
    """
    async with get_session() as session:
        try:
            # Check if the doctor is available at this time
            # Extract date and time components from appointment_date
            appt_date = appointment_date.date()
            appt_time = appointment_date.strftime("%H:%M")
            
            # Check for an availability entry that matches this date and time
            availability = session.exec(
                select(DoctorAvailability)
                .where(DoctorAvailability.doctor_id == doctor_id)
                .where(DoctorAvailability.date == appt_date)
                .where(DoctorAvailability.time == appt_time)
                .where(DoctorAvailability.is_available == True)
            ).first()
            
            if not availability:
                logger.warning(f"Doctor {doctor_id} is not available at {appointment_date}")
                return None
                
            # Check for conflicting appointments
            # For simplicity, we'll just check for exact time conflicts
            existing_appointment = session.exec(
                select(Appointment)
                .where(Appointment.doctor_id == doctor_id)
                .where(Appointment.appointment_date == appointment_date)
                .where(Appointment.status == "scheduled")
            ).first()
            
            if existing_appointment:
                logger.warning(f"Doctor {doctor_id} already has an appointment at {appointment_date}")
                return None
            
            # Create the appointment
            appointment = Appointment(
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_date=appointment_date,
                duration_minutes=duration_minutes,
                notes=notes
            )
            
            session.add(appointment)
            session.commit()
            session.refresh(appointment)
            
            # Get the full appointment details with patient and doctor
            app_read = AppointmentRead(
                id=appointment.id,
                patient_id=appointment.patient_id,
                doctor_id=appointment.doctor_id,
                appointment_date=appointment.appointment_date,
                duration_minutes=appointment.duration_minutes,
                status=appointment.status,
                notes=appointment.notes,
                created_at=appointment.created_at
            )
            return app_read
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            return None


async def get_next_available_slots(doctor_id: int, from_date: datetime, num_slots: int = 5) -> List[datetime]:
    """
    Get the next available appointment slots for a doctor
    
    Args:
        doctor_id: The ID of the doctor
        from_date: The date to start looking from
        num_slots: The number of slots to return
        
    Returns:
        List of available appointment datetimes
    """
    async with get_session() as session:
        try:
            # Get the doctor's availability from the given date
            availability = session.exec(
                select(DoctorAvailability)
                .where(DoctorAvailability.doctor_id == doctor_id)
                .where(DoctorAvailability.date >= from_date.date())
                .where(DoctorAvailability.is_available == True)
                .order_by(DoctorAvailability.date, DoctorAvailability.time)
            ).all()
            
            if not availability:
                return []
                
            # Get the doctor's scheduled appointments
            scheduled_appointments = session.exec(
                select(Appointment)
                .where(Appointment.doctor_id == doctor_id)
                .where(Appointment.appointment_date >= from_date)
                .where(Appointment.status == "scheduled")
            ).all()
            
            # Convert scheduled appointments to a set of datetime strings for easy checking
            booked_slots = {app.appointment_date.strftime("%Y-%m-%d %H:%M") for app in scheduled_appointments}
            
            # Generate available slots from availability data
            available_slots = []
            
            for slot in availability:
                # Convert availability to datetime
                hour, minute = map(int, slot.time.split(':'))
                slot_datetime = datetime.combine(slot.date, datetime.min.time().replace(hour=hour, minute=minute))
                
                # Skip if it's in the past
                if slot_datetime < from_date:
                    continue
                    
                # Check if this slot is already booked
                slot_str = slot_datetime.strftime("%Y-%m-%d %H:%M")
                if slot_str not in booked_slots:
                    available_slots.append(slot_datetime)
                    
                # Stop if we have enough slots
                if len(available_slots) >= num_slots:
                    break
            
            return available_slots
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []


async def get_appointment_details(appointment_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about an appointment
    
    Args:
        appointment_id: The ID of the appointment
        
    Returns:
        Dictionary with appointment details
    """
    async with get_session() as session:
        try:
            appointment = session.get(Appointment, appointment_id)
            if not appointment:
                return None
                
            # Get the doctor and patient
            doctor = session.get(Doctor, appointment.doctor_id)
            patient = session.get(Patient, appointment.patient_id) if appointment.patient_id else None
            
            # Get the doctor's specialty
            specialty = session.get(Specialty, doctor.specialty_id) if doctor else None
            
            # Build the response
            result = {
                "id": appointment.id,
                "date_time": appointment.appointment_date.strftime("%Y-%m-%d %H:%M"),
                "duration_minutes": appointment.duration_minutes,
                "status": appointment.status,
                "notes": appointment.notes,
                "doctor": {
                    "id": doctor.id,
                    "name": doctor.name,
                    "specialty": specialty.name if specialty else None
                } if doctor else None,
                "patient": {
                    "id": patient.id,
                    "name": patient.name
                } if patient else None
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting appointment details: {str(e)}")
            return None


async def get_all_doctors() -> List[DoctorRead]:
    """
    Get all doctors
    
    Returns:
        List of all doctors
    """
    async with get_session() as session:
        try:
            result = session.exec(select(Doctor)).all()
            return [DoctorRead(id=d.id, name=d.name, specialty_id=d.specialty_id, bio=d.bio) for d in result]
        except Exception as e:
            logger.error(f"Error getting doctors: {str(e)}")
            return []


async def get_specialty(specialty_id: int) -> Optional[SpecialtyRead]:
    """
    Get a specialty by ID
    
    Args:
        specialty_id: The ID of the specialty
        
    Returns:
        Specialty data, or None if not found
    """
    async with get_session() as session:
        try:
            result = session.get(Specialty, specialty_id)
            if not result:
                return None
                
            specialty_read = SpecialtyRead(
                id=result.id,
                name=result.name,
                description=result.description
            )
            return specialty_read
        except Exception as e:
            logger.error(f"Error getting specialty: {str(e)}")
            return None


async def add_appointment(
    patient_id: int,
    doctor_id: int,
    start_time: datetime,
    end_time: datetime,
    status: str = "scheduled",
    notes: Optional[str] = None
) -> Optional[AppointmentRead]:
    """
    Add a new appointment
    
    Args:
        patient_id: The ID of the patient
        doctor_id: The ID of the doctor
        start_time: The start time of the appointment
        end_time: The end time of the appointment
        status: The status of the appointment (default: "scheduled")
        notes: Optional notes for the appointment
        
    Returns:
        The created appointment with ID
    """
    async with get_session() as session:
        try:
            # Check if patient exists
            patient = session.get(Patient, patient_id)
            if not patient:
                logger.error(f"Patient not found: {patient_id}")
                return None
                
            # Check if doctor exists
            doctor = session.get(Doctor, doctor_id)
            if not doctor:
                logger.error(f"Doctor not found: {doctor_id}")
                return None
                
            # Create appointment
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                start_time=start_time,
                end_time=end_time,
                status=status,
                notes=notes
            )
            
            session.add(appointment)
            session.commit()
            session.refresh(appointment)
            
            app_read = AppointmentRead(
                id=appointment.id,
                patient_id=appointment.patient_id,
                doctor_id=appointment.doctor_id,
                appointment_date=appointment.appointment_date,
                duration_minutes=appointment.duration_minutes,
                status=appointment.status,
                notes=appointment.notes,
                created_at=appointment.created_at
            )
            return app_read
        except Exception as e:
            logger.error(f"Error adding appointment: {str(e)}")
            return None


async def find_doctor_by_name(doctor_name: str) -> Optional[DoctorRead]:
    """
    Find a doctor by name with flexible matching (includes partial matches and titles)
    
    Args:
        doctor_name: The name of the doctor to find (can include "Dr." prefix)
        
    Returns:
        The found doctor or None if not found
    """
    # Handle None values or empty strings
    if doctor_name is None or doctor_name.strip() == "":
        logger.error("Cannot search for doctor with empty name")
        return None
        
    try:
        async with get_session() as session:
            # Strip "Dr. " prefix if present for better matching
            search_name = doctor_name.replace("Dr.", "").strip()
            
            # Try exact match first (case insensitive)
            result = session.exec(select(Doctor).where(
                Doctor.name.ilike(f"%{search_name}%")
            )).first()
            
            if result:
                logger.info(f"Found doctor by name: {result.name}")
                
                # Get the specialty for the doctor
                specialty = session.get(Specialty, result.specialty_id)
                
                # Create the DoctorRead object
                doctor_read = DoctorRead(
                    id=result.id,
                    name=result.name, 
                    specialty_id=result.specialty_id,
                    bio=result.bio,
                    specialty=SpecialtyRead(
                        id=specialty.id,
                        name=specialty.name,
                        description=specialty.description
                    ) if specialty else None
                )
                return doctor_read
            
            # If no exact match, try matching on first name or last name
            # This is helpful when the user only provides partial information
            all_doctors = session.exec(select(Doctor)).all()
            
            for doctor in all_doctors:
                # Extract first and last name
                name_parts = doctor.name.split()
                
                # Try to match on first name or last name
                for part in name_parts:
                    if part.lower() in search_name.lower() or search_name.lower() in part.lower():
                        logger.info(f"Found doctor by partial name match: {doctor.name}")
                        
                        # Get the specialty for the doctor
                        specialty = session.get(Specialty, doctor.specialty_id)
                        
                        doctor_read = DoctorRead(
                            id=doctor.id,
                            name=doctor.name, 
                            specialty_id=doctor.specialty_id,
                            bio=doctor.bio,
                            specialty=SpecialtyRead(
                                id=specialty.id,
                                name=specialty.name,
                                description=specialty.description
                            ) if specialty else None
                        )
                        return doctor_read
            
            logger.warning(f"Doctor not found with name: {doctor_name}")
            return None
    except Exception as e:
        logger.error(f"Error finding doctor by name: {str(e)}")
        return None

async def find_specialty_by_name(specialty_name: str) -> Optional[SpecialtyRead]:
    """
    Find a specialty by name with flexible matching
    
    Args:
        specialty_name: The name of the specialty to find (can include parentheses)
        
    Returns:
        The found specialty or None if not found
    """
    # Handle None values or empty strings
    if specialty_name is None or specialty_name.strip() == "":
        logger.error("Cannot search for specialty with empty name")
        return None
        
    try:
        # Clean up the specialty name for better matching
        # Remove parentheses and common abbreviations
        clean_name = specialty_name.replace("(", "").replace(")", "").strip()
        
        # Handle common specialty abbreviations and alternative names
        specialty_mappings = {
            "ENT": "Otolaryngology",
            "Eye": "Ophthalmology",
            "Heart": "Cardiology",
            "Cardiac": "Cardiology",
            "Skin": "Dermatology",
            "Bone": "Orthopedics",
            "Joint": "Orthopedics",
            "Ortho": "Orthopedics",
            "Lung": "Pulmonology",
            "Respiratory": "Pulmonology",
            "Breathing": "Pulmonology",
            "Digestive": "Gastroenterology",
            "Stomach": "Gastroenterology",
            "GI": "Gastroenterology",
            "Brain": "Neurology",
            "Nerve": "Neurology",
            "Neuro": "Neurology"
        }
        
        async with get_session() as session:
            # First try exact match (case insensitive)
            result = session.exec(select(Specialty).where(
                Specialty.name.ilike(f"%{clean_name}%")
            )).first()
            
            if result:
                logger.info(f"Found specialty by name: {result.name}")
                return SpecialtyRead(id=result.id, name=result.name, description=result.description)
            
            # Next, try matching based on known mappings
            for key, value in specialty_mappings.items():
                if key.lower() in clean_name.lower():
                    # Look for the mapped specialty
                    mapped_result = session.exec(select(Specialty).where(
                        Specialty.name.ilike(f"%{value}%")
                    )).first()
                    
                    if mapped_result:
                        logger.info(f"Found specialty by mapping {key} to {mapped_result.name}")
                        return SpecialtyRead(id=mapped_result.id, name=mapped_result.name, description=mapped_result.description)
            
            # If still not found, try with all specialties
            all_specialties = session.exec(select(Specialty)).all()
            
            # Check if any word in the specialty name matches any word in the database specialties
            for specialty in all_specialties:
                specialty_words = specialty.name.lower().split()
                search_words = clean_name.lower().split()
                
                # Check for any word overlap
                if any(word in specialty_words for word in search_words) or any(word in search_words for word in specialty_words):
                    logger.info(f"Found specialty by word match: {specialty.name}")
                    return SpecialtyRead(id=specialty.id, name=specialty.name, description=specialty.description)
            
            logger.warning(f"Specialty not found with name: {specialty_name}")
            return None
    except Exception as e:
        logger.error(f"Error finding specialty by name: {str(e)}")
        return None 