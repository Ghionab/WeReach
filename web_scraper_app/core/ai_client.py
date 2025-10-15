"""
Gemini AI client for generating cold emails.
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from models.email_model import EmailContent
from utils.retry_manager import (
    RetryConfig, RetryStrategy, async_retry_on_failure,
    with_async_fallback, get_fallback_manager
)
from utils.exceptions import AIException, RetryableException


class AIException(Exception):
    """Base exception for AI service related errors."""
    pass


class AIAuthenticationException(AIException):
    """Exception for API authentication errors."""
    pass


class AIQuotaException(AIException):
    """Exception for API quota/rate limit errors."""
    pass


class AIServiceUnavailableException(AIException):
    """Exception for AI service unavailability."""
    pass


class GeminiAIClient:
    """Client for interacting with Gemini AI to generate cold emails."""
    
    def __init__(self, api_key: str, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the Gemini AI client.
        
        Args:
            api_key: The Gemini API key for authentication
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Initial delay between retries in seconds
        """
        self.api_key = api_key
        self.model = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        self.fallback_enabled = True
        
        # Register fallback mechanisms
        self._register_fallbacks()
        
        # Configure the API key
        if api_key:
            genai.configure(api_key=api_key)
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model with safety settings."""
        try:
            # Configure safety settings to be less restrictive for business emails
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                'gemini-pro',
                safety_settings=safety_settings
            )
            self.logger.info("Gemini AI model initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise AIException(f"Failed to initialize AI model: {str(e)}")
    
    def _register_fallbacks(self):
        """Register fallback mechanisms for AI operations."""
        fallback_manager = get_fallback_manager()
        
        # Register fallback for email generation
        fallback_manager.register_fallback(
            "generate_cold_email",
            self._fallback_generate_template_email,
            priority=1
        )
    
    async def _fallback_generate_template_email(self, website: str) -> EmailContent:
        """
        Fallback method that generates a basic template email when AI fails.
        
        Args:
            website: Website URL
            
        Returns:
            EmailContent with template email
        """
        self.logger.warning(f"Using fallback template email generation for {website}")
        
        # Extract domain from website for personalization
        try:
            from urllib.parse import urlparse
            domain = urlparse(website).netloc or website
            domain = domain.replace('www.', '')
        except:
            domain = website
        
        # Generate basic template email
        subject = f"Partnership Opportunity with {domain}"
        
        body = f"""Hello,

I hope this email finds you well. I came across {domain} and was impressed by your work.

I'd like to explore potential partnership opportunities that could be mutually beneficial for both our organizations.

Would you be available for a brief conversation to discuss this further?

Best regards,
[Your Name]
[Your Company]
[Your Contact Information]

---
This email was generated using a fallback template due to AI service unavailability.
"""
        
        return EmailContent(
            subject=subject,
            body=body,
            website=website
        )
    
    @async_retry_on_failure(RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=60.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retryable_exceptions=(AIException, RetryableException, Exception)
    ))
    @with_async_fallback("generate_cold_email")
    async def generate_cold_email(self, website: str) -> EmailContent:
        """
        Generate a personalized cold email for a website with retry logic.
        
        Args:
            website: The website URL to generate an email for
            
        Returns:
            EmailContent: Generated email with subject and body
            
        Raises:
            AIException: If email generation fails after all retries
        """
        if not self.model:
            raise AIException("AI model not initialized. Please check your API key.")
        
        # Use retry mechanism for email generation
        return await self._retry_with_backoff(
            self._generate_email_internal,
            website
        )
    
    async def _generate_email_internal(self, website: str) -> EmailContent:
        """
        Internal method to generate email without retry logic.
        
        Args:
            website: The website URL to generate an email for
            
        Returns:
            EmailContent: Generated email with subject and body
        """
        try:
            # Create structured prompt for professional cold email generation
            prompt = self._create_email_prompt(website)
            
            # Generate content using the model
            self.logger.info(f"Generating cold email for website: {website}")
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Parse the response
            if not response.text:
                raise AIException("AI service returned empty response")
            
            # Extract subject and body from response
            subject, body = self._parse_email_response(response.text)
            
            # Create and return EmailContent object
            email_content = EmailContent(
                subject=subject,
                body=body,
                website=website
            )
            
            self.logger.info(f"Successfully generated email for {website}")
            return email_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate email for {website}: {str(e)}")
            self._handle_api_error(e)
    
    def _create_email_prompt(self, website: str) -> str:
        """
        Create a structured prompt for email generation.
        
        Args:
            website: The website URL
            
        Returns:
            str: Formatted prompt for the AI model
        """
        prompt = f"""
Write a short, friendly, professional cold email for outreach to the owner of {website}. 
Make it persuasive but not spammy.

Requirements:
- Keep it concise (under 150 words)
- Be professional and respectful
- Include a clear value proposition
- Have a compelling subject line
- End with a clear call to action
- Avoid overly salesy language

Format your response exactly as follows:
SUBJECT: [Your subject line here]

BODY:
[Your email body here]

Website: {website}
"""
        return prompt
    
    def _parse_email_response(self, response_text: str) -> tuple[str, str]:
        """
        Parse the AI response to extract subject and body.
        
        Args:
            response_text: Raw response from AI model
            
        Returns:
            tuple: (subject, body) extracted from response
            
        Raises:
            AIException: If response format is invalid
        """
        try:
            lines = response_text.strip().split('\n')
            subject = ""
            body_lines = []
            in_body = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('SUBJECT:'):
                    subject = line.replace('SUBJECT:', '').strip()
                elif line.startswith('BODY:'):
                    in_body = True
                elif in_body and not line.startswith('Website:'):
                    if line:  # Skip empty lines
                        body_lines.append(line)
            
            body = '\n'.join(body_lines).strip()
            
            # Validate extracted content
            if not subject:
                raise AIException("Could not extract subject from AI response")
            if not body:
                raise AIException("Could not extract body from AI response")
            
            return subject, body
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {str(e)}")
            # Fallback: try to use the entire response as body with a generic subject
            fallback_subject = f"Partnership Opportunity"
            fallback_body = response_text.strip()
            return fallback_subject, fallback_body
    
    def test_connection(self) -> bool:
        """
        Test the connection to Gemini AI service.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            if not self.api_key:
                self.logger.error("No API key provided for connection test")
                return False
            
            if not self.model:
                self._initialize_model()
            
            # Test with a simple prompt
            test_prompt = "Say 'Connection successful' if you can read this."
            response = self.model.generate_content(test_prompt)
            
            if response.text and "successful" in response.text.lower():
                self.logger.info("Gemini AI connection test successful")
                return True
            else:
                self.logger.warning("Gemini AI connection test returned unexpected response")
                return False
                
        except Exception as e:
            self.logger.error(f"Gemini AI connection test failed: {str(e)}")
            return False
    
    def _handle_api_error(self, error: Exception):
        """
        Handle and categorize API errors with enhanced detection.
        
        Args:
            error: The original exception
            
        Raises:
            Appropriate AIException subclass based on error type
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Check for authentication errors
        auth_indicators = [
            "api key", "authentication", "unauthorized", "invalid key",
            "permission denied", "forbidden", "401", "403"
        ]
        if any(indicator in error_str for indicator in auth_indicators):
            raise AIAuthenticationException(
                "Invalid API key or authentication failed. Please check your Gemini API key in Settings."
            )
        
        # Check for quota/rate limit errors
        quota_indicators = [
            "quota", "rate limit", "too many requests", "429", "resource exhausted",
            "usage limit", "billing", "exceeded"
        ]
        if any(indicator in error_str for indicator in quota_indicators):
            raise AIQuotaException(
                "API quota exceeded or rate limit reached. Please wait and try again later."
            )
        
        # Check for service availability errors
        service_indicators = [
            "service unavailable", "timeout", "connection", "network", "502", "503", "504",
            "server error", "internal error", "temporarily unavailable", "maintenance"
        ]
        if any(indicator in error_str for indicator in service_indicators):
            raise AIServiceUnavailableException(
                "Gemini AI service is currently unavailable. Please try again in a few minutes."
            )
        
        # Check for content safety errors
        safety_indicators = [
            "safety", "blocked", "harmful", "inappropriate", "policy violation"
        ]
        if any(indicator in error_str for indicator in safety_indicators):
            raise AIException(
                "Content was blocked by safety filters. Try rephrasing your request or contact support."
            )
        
        # Generic error handling
        self.logger.error(f"Unhandled API error type: {error_type}, message: {error_str}")
        raise AIException(f"AI service error: {str(error)}")
    
    async def _retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with exponential backoff retry logic.
        
        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function call
            
        Raises:
            AIException: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
                
            except (AIQuotaException, AIServiceUnavailableException) as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Calculate exponential backoff delay
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries + 1} attempts failed")
                    
            except AIAuthenticationException as e:
                # Don't retry authentication errors
                self.logger.error(f"Authentication error, not retrying: {str(e)}")
                raise e
                
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed with unexpected error: {str(e)}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries + 1} attempts failed")
        
        # If we get here, all retries failed
        if self.fallback_enabled:
            self.logger.info("Attempting fallback email generation")
            return await self._generate_fallback_email(*args, **kwargs)
        else:
            raise last_exception or AIException("All retry attempts failed")
    
    async def _generate_fallback_email(self, website: str) -> EmailContent:
        """
        Generate a fallback email when AI service is unavailable.
        
        Args:
            website: The website URL to generate an email for
            
        Returns:
            EmailContent: Fallback email with generic content
        """
        try:
            # Extract domain name from website for personalization
            from urllib.parse import urlparse
            parsed_url = urlparse(website)
            domain = parsed_url.netloc or website
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Generate fallback email content
            subject = f"Partnership Opportunity with {domain.title()}"
            
            body = f"""Hello,

I hope this email finds you well. I came across {website} and was impressed by your work.

I believe there might be an opportunity for us to collaborate and create mutual value. I'd love to discuss how we might work together to achieve our shared goals.

Would you be open to a brief conversation to explore potential synergies?

Best regards"""
            
            self.logger.info(f"Generated fallback email for {website}")
            
            return EmailContent(
                subject=subject,
                body=body,
                website=website
            )
            
        except Exception as e:
            self.logger.error(f"Fallback email generation failed: {str(e)}")
            raise AIException(f"Both AI service and fallback generation failed: {str(e)}")
    
    def set_fallback_enabled(self, enabled: bool):
        """
        Enable or disable fallback email generation.
        
        Args:
            enabled: Whether to enable fallback generation
        """
        self.fallback_enabled = enabled
        self.logger.info(f"Fallback email generation {'enabled' if enabled else 'disabled'}")
    
    def get_retry_config(self) -> Dict[str, Any]:
        """
        Get current retry configuration.
        
        Returns:
            dict: Retry configuration settings
        """
        return {
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "fallback_enabled": self.fallback_enabled
        }
    
    def update_retry_config(self, max_retries: Optional[int] = None, 
                           retry_delay: Optional[float] = None):
        """
        Update retry configuration.
        
        Args:
            max_retries: New maximum retry count
            retry_delay: New initial retry delay
        """
        if max_retries is not None:
            self.max_retries = max(0, max_retries)
            self.logger.info(f"Updated max_retries to {self.max_retries}")
            
        if retry_delay is not None:
            self.retry_delay = max(0.1, retry_delay)
            self.logger.info(f"Updated retry_delay to {self.retry_delay}")
    
    def get_user_friendly_error_message(self, error: Exception) -> str:
        """
        Convert technical errors to user-friendly messages.
        
        Args:
            error: The exception to convert
            
        Returns:
            str: User-friendly error message
        """
        if isinstance(error, AIAuthenticationException):
            return (
                "Authentication failed. Please check your Gemini API key in the Settings tab. "
                "Make sure you have a valid API key from Google AI Studio."
            )
        elif isinstance(error, AIQuotaException):
            return (
                "API quota exceeded or rate limit reached. Please wait a few minutes and try again. "
                "If this persists, check your API usage limits in Google AI Studio."
            )
        elif isinstance(error, AIServiceUnavailableException):
            return (
                "The Gemini AI service is currently unavailable. Please try again in a few minutes. "
                "If the problem persists, check Google AI Studio status."
            )
        else:
            return (
                f"An unexpected error occurred while generating emails: {str(error)}. "
                "Please try again or contact support if the issue persists."
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            dict: Model information and status
        """
        return {
            "model_name": "gemini-pro",
            "api_key_configured": bool(self.api_key),
            "model_initialized": self.model is not None,
            "connection_status": "ready" if self.model else "not_initialized",
            "retry_config": self.get_retry_config()
        }