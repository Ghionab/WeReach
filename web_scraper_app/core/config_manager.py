"""
Configuration management system for the web scraper application.
Handles secure storage of API keys and SMTP credentials using system keyring.
"""
import json
import keyring
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import google.generativeai as genai
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from models.email_model import SMTPConfig


logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages application configuration with secure credential storage.
    
    Uses system keyring for sensitive data (API keys, passwords) and
    local JSON file for non-sensitive settings.
    """
    
    SERVICE_NAME = "WebScraperEmailAutomation"
    CONFIG_FILE = "config.json"
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_dir: Directory to store configuration files. 
                       Defaults to user's home directory/.web_scraper_config
        """
        if config_dir is None:
            config_dir = Path.home() / ".web_scraper_config"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file_path = self.config_dir / self.CONFIG_FILE
        
        # Load existing configuration
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from local file."""
        try:
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
        
        # Return default configuration
        return {
            "smtp_server": "",
            "smtp_port": 587,
            "smtp_email": "",
            "smtp_use_tls": True,
            "gemini_api_configured": False,
            "smtp_configured": False
        }
    
    def _save_config(self) -> None:
        """Save configuration to local file."""
        try:
            with open(self.config_file_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def set_gemini_api_key(self, api_key: str) -> None:
        """
        Securely store Gemini API key.
        
        Args:
            api_key: The Gemini API key to store
            
        Raises:
            ConfigurationError: If storing the key fails
        """
        try:
            keyring.set_password(self.SERVICE_NAME, "gemini_api_key", api_key)
            self._config["gemini_api_configured"] = True
            self._save_config()
            logger.info("Gemini API key stored successfully")
        except Exception as e:
            logger.error(f"Error storing Gemini API key: {e}")
            raise ConfigurationError(f"Failed to store Gemini API key: {e}")
    
    def get_gemini_api_key(self) -> Optional[str]:
        """
        Retrieve Gemini API key from secure storage.
        
        Returns:
            The stored API key or None if not found
        """
        try:
            return keyring.get_password(self.SERVICE_NAME, "gemini_api_key")
        except Exception as e:
            logger.error(f"Error retrieving Gemini API key: {e}")
            return None
    
    def set_smtp_config(self, smtp_config: SMTPConfig) -> None:
        """
        Store SMTP configuration with secure password storage.
        
        Args:
            smtp_config: SMTPConfig object with connection details
            
        Raises:
            ConfigurationError: If storing the configuration fails
        """
        try:
            # Store sensitive password in keyring
            keyring.set_password(self.SERVICE_NAME, "smtp_password", smtp_config.password)
            
            # Store non-sensitive settings in config file
            self._config.update({
                "smtp_server": smtp_config.server,
                "smtp_port": smtp_config.port,
                "smtp_email": smtp_config.email,
                "smtp_use_tls": smtp_config.use_tls,
                "smtp_configured": True
            })
            self._save_config()
            logger.info("SMTP configuration stored successfully")
        except Exception as e:
            logger.error(f"Error storing SMTP configuration: {e}")
            raise ConfigurationError(f"Failed to store SMTP configuration: {e}")
    
    def get_smtp_config(self) -> Optional[SMTPConfig]:
        """
        Retrieve SMTP configuration from storage.
        
        Returns:
            SMTPConfig object or None if not configured
        """
        try:
            if not self._config.get("smtp_configured", False):
                return None
            
            password = keyring.get_password(self.SERVICE_NAME, "smtp_password")
            if not password:
                logger.warning("SMTP password not found in keyring")
                return None
            
            return SMTPConfig(
                server=self._config["smtp_server"],
                port=self._config["smtp_port"],
                email=self._config["smtp_email"],
                password=password,
                use_tls=self._config["smtp_use_tls"]
            )
        except Exception as e:
            logger.error(f"Error retrieving SMTP configuration: {e}")
            return None
    
    def test_gemini_connection(self) -> tuple[bool, str]:
        """
        Test Gemini API connection and key validity.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            api_key = self.get_gemini_api_key()
            if not api_key:
                return False, "No Gemini API key configured"
            
            # Configure the API key
            genai.configure(api_key=api_key)
            
            # Test with a simple generation request
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Test connection")
            
            if response and response.text:
                return True, "Gemini API connection successful"
            else:
                return False, "Gemini API returned empty response"
                
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                return False, "Invalid Gemini API key"
            elif "quota" in error_msg.lower():
                return False, "Gemini API quota exceeded"
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return False, "Network connection error"
            else:
                return False, f"Gemini API error: {error_msg}"
    
    def test_smtp_connection(self) -> tuple[bool, str]:
        """
        Test SMTP connection with current configuration.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            smtp_config = self.get_smtp_config()
            if not smtp_config:
                return False, "No SMTP configuration found"
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Test connection
            if smtp_config.use_tls:
                server = smtplib.SMTP(smtp_config.server, smtp_config.port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(smtp_config.server, smtp_config.port, context=context)
            
            # Test authentication
            server.login(smtp_config.email, smtp_config.password)
            server.quit()
            
            return True, "SMTP connection successful"
            
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP authentication failed - check email and password"
        except smtplib.SMTPConnectError:
            return False, "Failed to connect to SMTP server - check server and port"
        except smtplib.SMTPServerDisconnected:
            return False, "SMTP server disconnected unexpectedly"
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                return False, "SMTP connection timeout - check server and port"
            elif "ssl" in error_msg.lower() or "tls" in error_msg.lower():
                return False, "SSL/TLS connection error - check security settings"
            else:
                return False, f"SMTP connection error: {error_msg}"
    
    def validate_configuration(self) -> Dict[str, tuple[bool, str]]:
        """
        Validate all configuration settings and connections.
        
        Returns:
            Dictionary with validation results for each component
        """
        results = {}
        
        # Test Gemini API
        gemini_success, gemini_msg = self.test_gemini_connection()
        results["gemini"] = (gemini_success, gemini_msg)
        
        # Test SMTP
        smtp_success, smtp_msg = self.test_smtp_connection()
        results["smtp"] = (smtp_success, smtp_msg)
        
        return results
    
    def is_fully_configured(self) -> bool:
        """
        Check if all required configurations are set up.
        
        Returns:
            True if both Gemini API and SMTP are configured
        """
        return (
            self._config.get("gemini_api_configured", False) and
            self._config.get("smtp_configured", False)
        )
    
    def get_configuration_status(self) -> Dict[str, bool]:
        """
        Get the configuration status for all components.
        
        Returns:
            Dictionary with configuration status for each component
        """
        return {
            "gemini_configured": self._config.get("gemini_api_configured", False),
            "smtp_configured": self._config.get("smtp_configured", False),
            "fully_configured": self.is_fully_configured()
        }
    
    def clear_gemini_config(self) -> None:
        """Clear Gemini API configuration."""
        try:
            keyring.delete_password(self.SERVICE_NAME, "gemini_api_key")
        except keyring.errors.PasswordDeleteError:
            pass  # Password not found, which is fine
        
        self._config["gemini_api_configured"] = False
        self._save_config()
        logger.info("Gemini API configuration cleared")
    
    def clear_smtp_config(self) -> None:
        """Clear SMTP configuration."""
        try:
            keyring.delete_password(self.SERVICE_NAME, "smtp_password")
        except keyring.errors.PasswordDeleteError:
            pass  # Password not found, which is fine
        
        self._config.update({
            "smtp_server": "",
            "smtp_port": 587,
            "smtp_email": "",
            "smtp_use_tls": True,
            "smtp_configured": False
        })
        self._save_config()
        logger.info("SMTP configuration cleared")
    
    def clear_all_config(self) -> None:
        """Clear all configuration data."""
        self.clear_gemini_config()
        self.clear_smtp_config()
        logger.info("All configuration data cleared")


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass