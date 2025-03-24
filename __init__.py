"""
Clinic-Mate: A voice-powered patient registration and appointment booking system
"""

import logging
import os

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'clinic-mate.log'))
    ]
)

__version__ = '1.0.0'
__author__ = 'Clinic-Mate Development Team' 