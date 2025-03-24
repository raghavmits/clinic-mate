"""
Utility functions for email handling, including formatting and sending emails.
"""

import logging
import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("email-utils")
logger.setLevel(logging.INFO)

def create_email_message(
    subject: str, 
    text_content: str, 
    html_content: str, 
    sender_email: str, 
    recipient_email: str
) -> MIMEMultipart:
    """
    Create an email message with both text and HTML versions
    
    Args:
        subject: Email subject line
        text_content: Plain text content for the email
        html_content: HTML content for the email
        sender_email: Email address of the sender
        recipient_email: Email address of the recipient
        
    Returns:
        Formatted email message ready to send
    """
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
                
    # Attach parts to the message
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    message.attach(part1)
    message.attach(part2)
    
    return message

def generate_html_email(content: str, title: str = "Assort Medical Clinic") -> str:
    """
    Generate a formatted HTML email with consistent styling
    
    Args:
        content: The main content to include in the email
        title: The title to display in the email header
        
    Returns:
        Formatted HTML string for the email
    """
    current_year = datetime.now().year
    
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #0066cc; }}
            h2 {{ color: #0066cc; margin-top: 20px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            .info-section {{ margin-bottom: 20px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #888; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <div class="info-section">
                <pre>{content}</pre>
            </div>
            <div class="footer">
                <p>This is an automated message from Clinic-Mate. Please do not reply to this email.</p>
                <p>© {current_year} Assort Clinic. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_email_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Get email credentials from environment variables
    
    Returns:
        Tuple containing (sender_email, password)
    """
    sender_email = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    
    if not sender_email:
        logger.warning("EMAIL_SENDER not set in environment variables")
    
    if not password:
        logger.warning("EMAIL_PASSWORD not set in environment variables")
    
    return sender_email, password

def send_email_sync(
    sender_email: str, 
    password: str, 
    recipient_email: str, 
    message_str: str
) -> bool:
    """
    Send an email using SMTP (synchronous function)
    
    Args:
        sender_email: Email address of the sender
        password: Password for the sender's email account
        recipient_email: Email address of the recipient
        message_str: Formatted email message as a string
        
    Returns:
        True if the email was sent successfully, False otherwise
    """
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, message_str)
        return True
    except Exception as e:
        logger.error(f"SMTP error: {str(e)}")
        return False 