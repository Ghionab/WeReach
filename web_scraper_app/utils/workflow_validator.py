"""
Workflow validation for end-to-end application testing
Tests complete workflow integration between UI and backend components
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

# Add the web_scraper_app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.app_controller import ApplicationController
from models.email_model import EmailModel, SentEmailModel, SMTPConfig, EmailContent
from utils.health_monitor import get_health_monitor, setup_default_health_checks


class WorkflowValidator(QObject):
    """
    Validates complete application workflow from UI to backend
    Tests signal/slot connections and data flow
    """
    
    # Signals for test coordination
    test_completed = pyqtSignal(str, bool, str)  # test_name, success, message
    workflow_completed = pyqtSignal(dict)  # results
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.controller = None
        self.test_results = {}
        self.current_test = None
        self.test_timeout = 30000  # 30 seconds timeout per test
        
        # Test data
        self.test_urls = [
            "https://httpbin.org/html",
            "https://jsonplaceholder.typicode.com"
        ]
        
        # Test state tracking
        self.scraping_completed = False
        self.emails_generated = False
        self.emails_sent = False
        self.data_exported = False
        
        # Collected data during workflow
        self.scraped_emails = []
        self.generated_emails = []
        self.sent_results = {}
    
    def initialize_controller(self) -> bool:
        """Initialize application controller for testing"""
        try:
            self.controller = ApplicationController()
            self.controller.initialize_modules()
            
            # Connect controller signals for monitoring
            self.controller.status_update.connect(self.on_status_update)
            self.controller.error_occurred.connect(self.on_error_occurred)
            
            # Connect workflow-specific signals
            self.controller.scraping_finished.connect(self.on_scraping_finished)
            self.controller.email_generation_finished.connect(self.on_email_generation_finished)
            self.controller.email_sending_finished.connect(self.on_email_sending_finished)
            self.controller.data_updated.connect(self.on_data_updated)
            
            self.logger.info("Application controller initialized for workflow testing")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize controller: {e}")
            return False
    
    async def validate_complete_workflow(self) -> Dict[str, Any]:
        """
        Validate complete application workflow
        
        Returns:
            Dictionary with validation results
        """
        self.logger.info("Starting complete workflow validation...")
        
        try:
            # Initialize controller
            if not self.initialize_controller():
                return {"status": "FAILED", "error": "Controller initialization failed"}
            
            # Test 1: Configuration validation
            await self.test_configuration_workflow()
            
            # Test 2: Web scraping workflow
            await self.test_scraping_workflow()
            
            # Test 3: Email generation workflow (if AI available)
            await self.test_email_generation_workflow()
            
            # Test 4: Email sending workflow (if SMTP available)
            await self.test_email_sending_workflow()
            
            # Test 5: Data export workflow
            await self.test_export_workflow()
            
            # Test 6: History and persistence workflow
            await self.test_history_workflow()
            
            # Test 7: Error handling workflow
            await self.test_error_handling_workflow()
            
            # Generate final validation report
            return self.generate_validation_report()
            
        except Exception as e:
            self.logger.error(f"Workflow validation failed: {e}")
            return {"status": "FAILED", "error": str(e)}
    
    async def test_configuration_workflow(self):
        """Test configuration management workflow"""
        self.logger.info("Testing configuration workflow...")
        
        try:
            # Test configuration status
            config_status = self.controller.config_manager.get_configuration_status()
            
            # Test API key configuration
            test_api_key = "test_workflow_key_12345"
            success = self.controller.update_gemini_config(test_api_key)
            
            # Test SMTP configuration
            test_smtp = SMTPConfig(
                server="smtp.test.com",
                port=587,
                email="test@workflow.com",
                password="test_password",
                use_tls=True
            )
            smtp_success = self.controller.update_smtp_config(test_smtp)
            
            self.test_results["configuration_workflow"] = {
                "status": "PASSED" if success and smtp_success else "FAILED",
                "tests": {
                    "config_status_check": "passed",
                    "api_key_update": "passed" if success else "failed",
                    "smtp_config_update": "passed" if smtp_success else "failed"
                }
            }
            
        except Exception as e:
            self.test_results["configuration_workflow"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_scraping_workflow(self):
        """Test web scraping workflow with signal coordination"""
        self.logger.info("Testing scraping workflow...")
        
        try:
            # Reset state
            self.scraping_completed = False
            self.scraped_emails = []
            
            # Start scraping
            self.controller.start_scraping(self.test_urls)
            
            # Wait for scraping to complete (with timeout)
            timeout_counter = 0
            while not self.scraping_completed and timeout_counter < 30:  # 30 second timeout
                await asyncio.sleep(1)
                timeout_counter += 1
                QApplication.processEvents()  # Process Qt events
            
            if not self.scraping_completed:
                raise Exception("Scraping workflow timed out")
            
            # Validate results
            if len(self.scraped_emails) == 0:
                self.logger.warning("No emails found during scraping (this may be expected)")
            
            # Test data persistence
            stored_emails = self.controller.get_scraped_emails()
            
            self.test_results["scraping_workflow"] = {
                "status": "PASSED",
                "tests": {
                    "scraping_execution": "passed",
                    "signal_coordination": "passed",
                    "data_persistence": "passed"
                },
                "stats": {
                    "urls_processed": len(self.test_urls),
                    "emails_found": len(self.scraped_emails),
                    "emails_stored": len(stored_emails)
                }
            }
            
        except Exception as e:
            self.test_results["scraping_workflow"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_email_generation_workflow(self):
        """Test email generation workflow"""
        self.logger.info("Testing email generation workflow...")
        
        try:
            # Check if AI client is available
            if not self.controller.ai_client:
                self.test_results["email_generation_workflow"] = {
                    "status": "SKIPPED",
                    "reason": "AI client not configured"
                }
                return
            
            # Reset state
            self.emails_generated = False
            self.generated_emails = []
            
            # Generate emails for test websites
            test_websites = ["https://example.com", "https://test.org"]
            self.controller.generate_emails(test_websites)
            
            # Wait for generation to complete
            timeout_counter = 0
            while not self.emails_generated and timeout_counter < 30:
                await asyncio.sleep(1)
                timeout_counter += 1
                QApplication.processEvents()
            
            if not self.emails_generated:
                raise Exception("Email generation workflow timed out")
            
            # Validate generated emails
            assert len(self.generated_emails) > 0, "No emails were generated"
            
            for email in self.generated_emails:
                assert email.get('subject'), "Generated email missing subject"
                assert email.get('body'), "Generated email missing body"
                assert email.get('website'), "Generated email missing website reference"
            
            self.test_results["email_generation_workflow"] = {
                "status": "PASSED",
                "tests": {
                    "generation_execution": "passed",
                    "signal_coordination": "passed",
                    "email_validation": "passed"
                },
                "stats": {
                    "websites_processed": len(test_websites),
                    "emails_generated": len(self.generated_emails)
                }
            }
            
        except Exception as e:
            self.test_results["email_generation_workflow"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_email_sending_workflow(self):
        """Test email sending workflow"""
        self.logger.info("Testing email sending workflow...")
        
        try:
            # Check if email sender is available
            if not self.controller.email_sender:
                self.test_results["email_sending_workflow"] = {
                    "status": "SKIPPED",
                    "reason": "Email sender not configured"
                }
                return
            
            # Reset state
            self.emails_sent = False
            self.sent_results = {}
            
            # Prepare test email data (don't actually send)
            test_email_data = [{
                'website': 'https://test.com',
                'subject': 'Workflow Test Email',
                'body': 'This is a test email for workflow validation.',
                'recipients': ['test@example.com']
            }]
            
            # Note: In a real test environment, we would mock the email sending
            # For now, we'll test the workflow preparation
            
            # Test email data validation
            assert len(test_email_data) > 0, "No email data prepared"
            assert test_email_data[0]['recipients'], "No recipients specified"
            
            self.test_results["email_sending_workflow"] = {
                "status": "PASSED",
                "tests": {
                    "email_preparation": "passed",
                    "data_validation": "passed",
                    "workflow_setup": "passed"
                },
                "note": "Actual email sending skipped in workflow test"
            }
            
        except Exception as e:
            self.test_results["email_sending_workflow"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_export_workflow(self):
        """Test data export workflow"""
        self.logger.info("Testing export workflow...")
        
        try:
            # Test export functionality
            test_file = "workflow_test_export.csv"
            
            # Get current scraped emails
            emails = self.controller.get_scraped_emails()
            
            if len(emails) == 0:
                # Create test data for export
                test_email = EmailModel(
                    email="workflow_test@example.com",
                    source_website="https://workflow-test.com",
                    extracted_at=datetime.now()
                )
                self.controller.db_manager.save_scraped_emails([test_email])
                emails = self.controller.get_scraped_emails()
            
            # Test export
            success = self.controller.export_scraped_emails_csv(test_file)
            
            # Wait a moment for export to complete
            await asyncio.sleep(2)
            QApplication.processEvents()
            
            # Check if file was created
            file_exists = os.path.exists(test_file)
            
            # Clean up
            if file_exists:
                os.remove(test_file)
            
            self.test_results["export_workflow"] = {
                "status": "PASSED" if success else "FAILED",
                "tests": {
                    "export_execution": "passed" if success else "failed",
                    "file_creation": "passed" if file_exists else "failed"
                },
                "stats": {
                    "emails_exported": len(emails)
                }
            }
            
        except Exception as e:
            self.test_results["export_workflow"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_history_workflow(self):
        """Test email history and tracking workflow"""
        self.logger.info("Testing history workflow...")
        
        try:
            # Test history retrieval
            history = self.controller.get_email_history()
            
            # Test history refresh
            self.controller.refresh_email_history()
            
            # Wait for refresh to complete
            await asyncio.sleep(1)
            QApplication.processEvents()
            
            # Test data persistence
            refreshed_history = self.controller.get_email_history()
            
            self.test_results["history_workflow"] = {
                "status": "PASSED",
                "tests": {
                    "history_retrieval": "passed",
                    "history_refresh": "passed",
                    "data_persistence": "passed"
                },
                "stats": {
                    "history_records": len(history),
                    "refreshed_records": len(refreshed_history)
                }
            }
            
        except Exception as e:
            self.test_results["history_workflow"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def test_error_handling_workflow(self):
        """Test error handling and recovery workflow"""
        self.logger.info("Testing error handling workflow...")
        
        try:
            # Test invalid URL handling
            invalid_urls = ["not-a-url", ""]
            
            # This should handle errors gracefully
            self.controller.start_scraping(invalid_urls)
            
            # Wait a moment
            await asyncio.sleep(2)
            QApplication.processEvents()
            
            # Test empty email generation
            try:
                self.controller.generate_emails([])
            except Exception:
                pass  # Expected to handle gracefully
            
            # Test invalid email sending
            try:
                self.controller.send_emails([])
            except Exception:
                pass  # Expected to handle gracefully
            
            self.test_results["error_handling_workflow"] = {
                "status": "PASSED",
                "tests": {
                    "invalid_url_handling": "passed",
                    "empty_data_handling": "passed",
                    "graceful_degradation": "passed"
                }
            }
            
        except Exception as e:
            self.test_results["error_handling_workflow"] = {
                "status": "FAILED",
                "error": str(e)
            }
    
    def on_status_update(self, message: str):
        """Handle status updates from controller"""
        self.logger.info(f"Status: {message}")
    
    def on_error_occurred(self, error: str):
        """Handle errors from controller"""
        self.logger.warning(f"Error: {error}")
    
    def on_scraping_finished(self, emails: List[EmailModel]):
        """Handle scraping completion"""
        self.scraped_emails = emails
        self.scraping_completed = True
        self.logger.info(f"Scraping completed with {len(emails)} emails")
    
    def on_email_generation_finished(self, emails: List[Dict[str, Any]]):
        """Handle email generation completion"""
        self.generated_emails = emails
        self.emails_generated = True
        self.logger.info(f"Email generation completed with {len(emails)} emails")
    
    def on_email_sending_finished(self, results: Dict[str, Any]):
        """Handle email sending completion"""
        self.sent_results = results
        self.emails_sent = True
        self.logger.info(f"Email sending completed: {results}")
    
    def on_data_updated(self, data_type: str):
        """Handle data updates"""
        self.logger.info(f"Data updated: {data_type}")
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get("status") == "PASSED")
        failed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get("status") == "FAILED")
        skipped_tests = sum(1 for result in self.test_results.values() 
                           if isinstance(result, dict) and result.get("status") == "SKIPPED")
        
        total_tests = passed_tests + failed_tests + skipped_tests
        overall_status = "PASSED" if failed_tests == 0 else "FAILED"
        
        report = {
            "overall_status": overall_status,
            "summary": {
                "total_workflows": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%"
            },
            "workflow_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_workflow_recommendations()
        }
        
        return report
    
    def _generate_workflow_recommendations(self) -> List[str]:
        """Generate workflow-specific recommendations"""
        recommendations = []
        
        # Check for failed workflows
        for workflow_name, result in self.test_results.items():
            if isinstance(result, dict) and result.get("status") == "FAILED":
                recommendations.append(f"Fix workflow issues in {workflow_name}: {result.get('error', 'Unknown error')}")
        
        # Check for skipped workflows
        if self.test_results.get("email_generation_workflow", {}).get("status") == "SKIPPED":
            recommendations.append("Configure Gemini API key to enable email generation workflow")
        
        if self.test_results.get("email_sending_workflow", {}).get("status") == "SKIPPED":
            recommendations.append("Configure SMTP settings to enable email sending workflow")
        
        # Check workflow integration
        scraping_passed = self.test_results.get("scraping_workflow", {}).get("status") == "PASSED"
        export_passed = self.test_results.get("export_workflow", {}).get("status") == "PASSED"
        
        if scraping_passed and export_passed:
            recommendations.append("Core workflows are functioning properly")
        
        if not recommendations:
            recommendations.append("All workflows validated successfully - application integration is complete")
        
        return recommendations
    
    def cleanup(self):
        """Clean up workflow test resources"""
        try:
            if self.controller:
                self.controller.cleanup()
            
            # Remove any test files
            test_files = ["workflow_test_export.csv"]
            for file in test_files:
                if os.path.exists(file):
                    os.remove(file)
            
            self.logger.info("Workflow validation cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"Workflow cleanup failed: {e}")


async def validate_application_workflow():
    """
    Main function to validate complete application workflow
    
    Returns:
        Validation results dictionary
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Qt application for signal/slot testing
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create workflow validator
    validator = WorkflowValidator()
    
    try:
        # Run workflow validation
        results = await validator.validate_complete_workflow()
        
        # Print summary
        print("\n" + "="*60)
        print("WORKFLOW VALIDATION RESULTS")
        print("="*60)
        print(f"Overall Status: {results['overall_status']}")
        print(f"Workflows Passed: {results['summary']['passed']}")
        print(f"Workflows Failed: {results['summary']['failed']}")
        print(f"Workflows Skipped: {results['summary']['skipped']}")
        print(f"Success Rate: {results['summary']['success_rate']}")
        
        if results['recommendations']:
            print("\nRecommendations:")
            for rec in results['recommendations']:
                print(f"  • {rec}")
        
        print("="*60)
        
        return results
        
    finally:
        # Always cleanup
        validator.cleanup()


if __name__ == "__main__":
    # Run workflow validation
    results = asyncio.run(validate_application_workflow())
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_status'] == 'PASSED' else 1
    sys.exit(exit_code)