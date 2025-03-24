"""
Utility functions for handling dates and times throughout the application.
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple

logger = logging.getLogger("date-utils")
logger.setLevel(logging.INFO)

# Standard date formats the application will try to parse
DATE_FORMATS = [
    "%A, %B %d, %Y at %I:%M %p",  # Monday, January 1, 2023 at 9:00 AM
    "%B %d, %Y at %I:%M %p",      # January 1, 2023 at 9:00 AM
    "%Y-%m-%d %H:%M",             # 2023-01-01 09:00
    "%m/%d/%Y %H:%M",             # 01/01/2023 09:00
    "%m/%d/%Y %I:%M %p",          # 01/01/2023 9:00 AM
    "%A, %B %d, %Y",              # Monday, January 1, 2023 (defaults to 9:00 AM)
    "%B %d, %Y",                  # January 1, 2023 (defaults to 9:00 AM)
    "%m/%d/%Y",                   # 01/01/2023 (defaults to 9:00 AM)
    "%Y-%m-%d",                   # 2023-01-01 (defaults to 9:00 AM)
]

# Month names to number mapping for natural language processing
MONTH_MAPPING = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def parse_date_time(date_time_str: str) -> Tuple[Optional[datetime], bool]:
    """
    Parse a date/time string into a datetime object using multiple formats
    
    Args:
        date_time_str: The date/time string to parse
        
    Returns:
        Tuple containing (parsed_datetime, success_flag)
    """
    # Try standard formats first
    for fmt in DATE_FORMATS:
        try:
            parsed_date = datetime.strptime(date_time_str, fmt)
            return parsed_date, True
        except ValueError:
            continue
    
    # Try natural language parsing for month names
    try:
        date_time_str = date_time_str.lower()
        
        # Check for month names in the string
        detected_month = None
        month_value = None
        
        for month_name, month_num in MONTH_MAPPING.items():
            if month_name in date_time_str:
                detected_month = month_name
                month_value = month_num
                break
        
        if detected_month:
            # Extract day from the string
            day_parts = [p for p in date_time_str.replace(",", "").split() if p.isdigit()]
            if day_parts:
                day = int(day_parts[0])
                
                # Extract year if present, otherwise use next year
                year_parts = [p for p in date_time_str.replace(",", "").split() 
                             if p.isdigit() and len(p) == 4]
                if year_parts:
                    year = int(year_parts[0])
                else:
                    # Default to next year for future appointments
                    current_year = datetime.now().year
                    if datetime.now().month > month_value:
                        year = current_year + 1
                    else:
                        year = current_year
                
                # Default to 9:00 AM if no time specified
                parsed_date = datetime(year, month_value, day, 9, 0)
                return parsed_date, True
    except Exception as e:
        logger.error(f"Error in natural language date parsing: {str(e)}")
    
    # If all parsing attempts fail
    return None, False

def format_date_for_display(dt: datetime) -> str:
    """
    Format a datetime object for display in a user-friendly format
    
    Args:
        dt: The datetime object to format
        
    Returns:
        Formatted date string
    """
    return dt.strftime("%A, %B %d, %Y at %I:%M %p")

def is_date_in_future(dt: datetime) -> bool:
    """
    Check if a datetime is in the future
    
    Args:
        dt: The datetime to check
        
    Returns:
        True if the datetime is in the future, False otherwise
    """
    return dt > datetime.now()

def parse_date_of_birth(dob_str: str) -> Optional[datetime.date]:
    """
    Parse a date of birth string into a date object
    
    Args:
        dob_str: The date of birth string to parse
        
    Returns:
        Parsed date or None if parsing fails
    """
    try:
        # Try common formats for DOB
        for fmt in [
            "%m/%d/%Y",     # MM/DD/YYYY
            "%Y-%m-%d",     # YYYY-MM-DD
            "%B %d, %Y"     # Month DD, YYYY
        ]:
            try:
                return datetime.strptime(dob_str, fmt).date()
            except ValueError:
                continue
        
        # If standard formats fail, return None
        return None
    except Exception as e:
        logger.error(f"Error parsing date of birth: {str(e)}")
        return None 