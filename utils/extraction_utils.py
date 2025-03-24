"""
Utility functions for extracting information from conversation history.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger("extraction-utils")
logger.setLevel(logging.INFO)

# Define regex patterns for common data extractions
PATTERNS = {
    'name': [
        r"[Mm]y name is ([A-Za-z\s.',-]+)",
        r"[Nn]ame is ([A-Za-z\s.',-]+)",
        r"[Nn]ame: ([A-Za-z\s.',-]+)",
        r"[Cc]all me ([A-Za-z\s.',-]+)",
        r"[Tt]his is ([A-Za-z\s.',-]+)",
        r"[Ii]'m ([A-Za-z\s.',-]+)"
    ],
    'dob': [
        r"[Bb]orn on (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"[Bb]irthday is (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"[Dd]ate of [Bb]irth:? (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"[Bb]irth date:? (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"[Dd][Oo][Bb]:? (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"[Bb]orn (?:on|in) ([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})",
        r"[Bb]orn (?:on|in) ([A-Za-z]+ \d{1,2},? \d{4})"
    ],
    'phone': [
        r"[Pp]hone(?:\s+[Nn]umber)? is (\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"[Pp]hone(?:\s+[Nn]umber)?:? (\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"[Cc]all me at (\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"[Mm]y number is (\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
    ],
    'email': [
        r"[Ee]mail is ([\w.-]+@[\w.-]+\.\w+)",
        r"[Ee]mail:? ([\w.-]+@[\w.-]+\.\w+)",
        r"[Cc]ontact me at ([\w.-]+@[\w.-]+\.\w+)"
    ],
    'insurance': [
        r"[Ii]nsurance(?:\s+[Pp]rovider)? is ([A-Za-z\s&.,-]+)",
        r"[Ii]nsurance(?:\s+[Pp]rovider)?:? ([A-Za-z\s&.,-]+)",
        r"[Ii] have ([A-Za-z\s&.,-]+) insurance",
        r"[Cc]overed by ([A-Za-z\s&.,-]+)"
    ],
    'insurance_id': [
        r"[Ii]nsurance [Ii][Dd](?:\s+[Nn]umber)? is ([A-Za-z0-9\s-]+)",
        r"[Ii]nsurance [Ii][Dd](?:\s+[Nn]umber)?:? ([A-Za-z0-9\s-]+)",
        r"[Ii][Dd] [Nn]umber is ([A-Za-z0-9\s-]+)",
        r"[Pp]olicy [Nn]umber:? ([A-Za-z0-9\s-]+)"
    ],
    'medical_complaint': [
        r"[Hh]ere because of ([^.!?]+)",
        r"[Pp]roblem is ([^.!?]+)",
        r"[Ii]ssue is ([^.!?]+)",
        r"[Cc]omplaint is ([^.!?]+)",
        r"[Ss]uffering from ([^.!?]+)",
        r"[Hh]aving ([^.!?]+)"
    ],
    'address': [
        r"[Aa]ddress is ([A-Za-z0-9\s.,#-]+)",
        r"[Aa]ddress:? ([A-Za-z0-9\s.,#-]+)",
        r"[Ll]ive at ([A-Za-z0-9\s.,#-]+)",
        r"[Rr]eside at ([A-Za-z0-9\s.,#-]+)"
    ]
}

def extract_data_from_conversation(
    conversation: List[Dict[str, str]], 
    data_type: str
) -> Optional[str]:
    """
    Extract specific information from conversation history
    
    Args:
        conversation: List of conversation messages with 'role' and 'content' keys
        data_type: Type of data to extract (name, dob, phone, email, etc.)
        
    Returns:
        Extracted information or None if not found
    """
    if data_type not in PATTERNS:
        logger.warning(f"Unknown data type for extraction: {data_type}")
        return None
    
    # Only process user messages
    user_messages = [msg["content"] for msg in conversation if msg.get("role") == "user"]
    
    for message in user_messages:
        for pattern in PATTERNS[data_type]:
            match = re.search(pattern, message)
            if match:
                extracted = match.group(1).strip()
                logger.info(f"Extracted {data_type} from conversation: {extracted}")
                return extracted
    
    logger.warning(f"Could not extract {data_type} from conversation history")
    return None

def extract_multiple_data_types(
    conversation: List[Dict[str, str]], 
    data_types: List[str]
) -> Dict[str, Optional[str]]:
    """
    Extract multiple types of information from conversation history
    
    Args:
        conversation: List of conversation messages
        data_types: List of data types to extract
        
    Returns:
        Dictionary of extracted information by data type
    """
    results = {}
    
    for data_type in data_types:
        results[data_type] = extract_data_from_conversation(conversation, data_type)
    
    return results

def extract_all_patient_data(
    conversation: List[Dict[str, str]]
) -> Dict[str, Optional[str]]:
    """
    Extract all relevant patient data from conversation history
    
    Args:
        conversation: List of conversation messages
        
    Returns:
        Dictionary of all extracted patient information
    """
    data_types = ['name', 'dob', 'phone', 'email', 'insurance', 
                 'insurance_id', 'medical_complaint', 'address']
    
    return extract_multiple_data_types(conversation, data_types)

def clean_extracted_data(data: str, data_type: str) -> str:
    """
    Clean extracted data to ensure it's in a consistent format
    
    Args:
        data: Raw extracted data
        data_type: Type of data being cleaned
        
    Returns:
        Cleaned data in a consistent format
    """
    if not data:
        return data
    
    if data_type == 'phone':
        # Strip all non-numeric characters and format as (XXX) XXX-XXXX
        digits = re.sub(r'\D', '', data)
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        return data
    
    if data_type == 'email':
        # Lowercase email addresses
        return data.lower()
    
    if data_type in ['name', 'insurance', 'medical_complaint']:
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in data.split())
    
    # Return as is for other types
    return data 