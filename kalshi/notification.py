import os
import logging
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

_logger = logging.getLogger(__name__)

class TwilioClient:
    """Client for interacting with the Twilio API to send messages."""

    def __init__(self):
        """Initialize the Twilio client with credentials from environment variables."""
        load_dotenv()
        
        # Get Twilio credentials from environment variables
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_phone = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # Validate required credentials
        if not all([self.account_sid, self.auth_token, self.from_phone]):
            _logger.error('Missing Twilio credentials in environment variables')
            raise ValueError(
                'Missing Twilio credentials. Please set TWILIO_ACCOUNT_SID, '
                'TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env file'
            )
        
        # Initialize the Twilio client
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_message(
        self, 
        to_phone: str, 
        message: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS or MMS message using Twilio.
        
        Args:
            to_phone: Recipient phone number in E.164 format (+1xxxxxxxxxx)
            message: Text content of the message
            media_urls: Optional list of media URLs to include (for MMS)
            
        Returns:
            Dictionary containing the Twilio message object
            
        Raises:
            TwilioRestException: If the API request fails
        """
        _logger.info(f'Sending message to {to_phone}')
        
        try:
            # Create message
            message_params = {
                'to': to_phone,
                'from_': self.from_phone,
                'body': message
            }
            
            # Add media URLs if provided (for MMS)
            if media_urls:
                message_params['media_urls'] = media_urls
            
            # Send message through Twilio API
            message_obj = self.client.messages.create(**message_params)
            
            _logger.info(f'Message sent successfully: {message_obj.sid}')
            return {
                'sid': message_obj.sid,
                'status': message_obj.status,
                'error_code': message_obj.error_code,
                'error_message': message_obj.error_message,
                'to': message_obj.to,
                'from_': message_obj.from_,
                'date_created': str(message_obj.date_created),
                'date_sent': str(message_obj.date_sent),
                'price': message_obj.price,
                'price_unit': message_obj.price_unit
            }
        
        except TwilioRestException as e:
            _logger.error(f'Twilio API error: {e.msg}')
            raise
        except Exception as e:
            _logger.error(f'Failed to send message: {str(e)}')
            raise
    
    def send_bulk_messages(
        self, 
        to_phones: List[str], 
        message: str,
        media_urls: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Send the same message to multiple recipients.
        
        Args:
            to_phones: List of recipient phone numbers in E.164 format
            message: Text content of the message
            media_urls: Optional list of media URLs to include (for MMS)
            
        Returns:
            List of dictionaries containing the Twilio message objects
        """
        results = []
        for phone in to_phones:
            try:
                result = self.send_message(phone, message, media_urls)
                results.append(result)
            except Exception as e:
                _logger.error(f'Failed to send message to {phone}: {str(e)}')
                results.append({'error': str(e), 'to': phone})
        
        return results
 