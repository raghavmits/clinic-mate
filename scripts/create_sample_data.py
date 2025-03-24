#!/usr/bin/env python3
"""
Script to create sample data for the clinic-mate application including:
- Medical specialties
- Doctors with their specialties
- Doctor availabilities

Usage:
    python create_sample_data.py
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
import os
import random  # Add this import at the top with other imports

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create-sample-data")

# Sample specialty data
SPECIALTIES = [
    {"name": "Cardiology", "description": "Heart and blood vessel disorders"},
    {"name": "Ophthalmology", "description": "Eye disorders and vision care"},
    {"name": "Otolaryngology", "description": "Ear, nose, and throat disorders (ENT)"},
    {"name": "Orthopedics", "description": "Bone and joint disorders"},
    {"name": "Neurology", "description": "Brain, spinal cord, and nerve disorders"},
    {"name": "Dermatology", "description": "Skin disorders"},
    {"name": "Pulmonology", "description": "Lung and respiratory disorders"},
    {"name": "Gastroenterology", "description": "Digestive system disorders"}
]

# Sample doctor data - will be populated with specialty IDs
DOCTORS = [
    # Cardiology
    {"name": "Dr. Jane Smith", "specialty": "Cardiology", "bio": "Specializes in cardiovascular surgery with 15 years of experience"},
    {"name": "Dr. Robert Johnson", "specialty": "Cardiology", "bio": "Expert in cardiac rehabilitation"},
    
    # Ophthalmology
    {"name": "Dr. Sarah Chen", "specialty": "Ophthalmology", "bio": "Specializes in retinal surgery"},
    {"name": "Dr. Michael Torres", "specialty": "Ophthalmology", "bio": "Focused on pediatric eye care"},
    
    # ENT
    {"name": "Dr. Emily Wilson", "specialty": "Otolaryngology", "bio": "Specializes in voice and swallowing disorders"},
    {"name": "Dr. William Davis", "specialty": "Otolaryngology", "bio": "Expert in sinus surgery"},
    
    # Orthopedics
    {"name": "Dr. David Lee", "specialty": "Orthopedics", "bio": "Specializes in sports medicine and joint replacement"},
    {"name": "Dr. Jennifer White", "specialty": "Orthopedics", "bio": "Focus on spinal disorders"},
    
    # Neurology
    {"name": "Dr. Richard Brown", "specialty": "Neurology", "bio": "Specializes in stroke treatment and prevention"},
    {"name": "Dr. Rebecca Martinez", "specialty": "Neurology", "bio": "Expert in headache and migraine management"},
    
    # Dermatology
    {"name": "Dr. Thomas Jackson", "specialty": "Dermatology", "bio": "Specializes in skin cancer detection and treatment"},
    {"name": "Dr. Lisa Kim", "specialty": "Dermatology", "bio": "Focus on pediatric dermatology"},
    
    # Pulmonology
    {"name": "Dr. Mark Thompson", "specialty": "Pulmonology", "bio": "Specializes in asthma and COPD management"},
    {"name": "Dr. Elizabeth Clark", "specialty": "Pulmonology", "bio": "Expert in sleep apnea and sleep disorders"},
    
    # Gastroenterology
    {"name": "Dr. Anthony Rodriguez", "specialty": "Gastroenterology", "bio": "Specializes in inflammatory bowel disease"},
    {"name": "Dr. Michelle Patel", "specialty": "Gastroenterology", "bio": "Focus on liver disorders"}
]

# Default availability - each doctor will have these time slots
DEFAULT_AVAILABILITY = [
    # Each doctor will have hourly slots over the next two weeks
    # Format: { "time": "HH:MM" }
    {"time": "09:00"},
    {"time": "10:00"},
    {"time": "11:00"},
    {"time": "13:00"},
    {"time": "14:00"},
    {"time": "15:00"},
    {"time": "16:00"}
]

async def create_data():
    # Initialize database
    database.create_db_and_tables()
    logger.info("Database initialized")
    
    # Create specialties
    specialty_map = {}
    for specialty_data in SPECIALTIES:
        specialty = await database.add_specialty(
            name=specialty_data["name"],
            description=specialty_data["description"]
        )
        if specialty:
            logger.info(f"Created specialty: {specialty.name}")
            specialty_map[specialty.name] = specialty.id
        else:
            logger.error(f"Failed to create specialty: {specialty_data['name']}")
    
    # Create doctors
    doctor_map = {}
    for doctor_data in DOCTORS:
        specialty_id = specialty_map.get(doctor_data["specialty"])
        if not specialty_id:
            logger.error(f"Specialty not found: {doctor_data['specialty']}")
            continue
            
        doctor = await database.add_doctor(
            name=doctor_data["name"],
            specialty_id=specialty_id,
            bio=doctor_data["bio"]
        )
        
        if doctor:
            logger.info(f"Created doctor: {doctor.name}")
            doctor_map[doctor.name] = doctor.id
        else:
            logger.error(f"Failed to create doctor: {doctor_data['name']}")
    
    # Create availabilities
    for doctor_name, doctor_id in doctor_map.items():
        start_date = datetime.now().date()
        
        # Randomly select 3-5 days from the available weekdays
        available_days = [d for d in range(8, 14) if (start_date + timedelta(days=d)).weekday() < 5]
        selected_days = random.sample(available_days, k=random.randint(2, 3))
        
        for day_offset in selected_days:
            current_date = start_date + timedelta(days=day_offset)
            
            # Randomly select 2-4 time slots for each day
            selected_times = random.sample(DEFAULT_AVAILABILITY, k=random.randint(2, 4))
            
            for avail in selected_times:
                success = await database.add_doctor_availability(
                    doctor_id=doctor_id,
                    availability_date=current_date,
                    availability_time=avail["time"],
                    is_available=True
                )
                
                if success:
                    logger.info(f"Added availability for {doctor_name}: {current_date} at {avail['time']}")
                else:
                    logger.error(f"Failed to add availability for {doctor_name}")
    
    logger.info("Sample data creation complete!")

if __name__ == "__main__":
    asyncio.run(create_data()) 