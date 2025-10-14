#!/usr/bin/env python3
"""
Web Scraper Email Automation Tool
Main application entry point
"""

import sys
import os
import logging
import asyncio
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Add the web_scraper_app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web_scraper_app'))

from ui.main_window import MainWindow
from core.app_controller import ApplicationController
from utils.health_monitor import get_health_monitor, setup_default_health_checks
from utils.logger import setup_logging as setup_app_logging
from utils.performance_optimizer import setup_performance_optimizations, get_resource_manager


def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('web_scraper_app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


async def perform_startup_validation():
    """Perform startup health checks and validation."""
    try:
        # Setup default health checks
        setup_default_health_checks()
        
        # Get health monitor
        health_monitor = get_health_monitor()
        
        # Perform startup validation
        success, critical_issues = await health_monitor.startup_validation()
        
        if not success:
            error_msg = "Critical startup issues detected:\n" + "\n".join(critical_issues)
            logging.error(error_msg)
            return False, error_msg
        
        # Log health summary
        health_summary = health_monitor.get_health_summary()
        logging.info(f"Startup validation passed - {health_summary['healthy_components']} components healthy, "
                    f"{health_summary['warning_components']} warnings")
        
        return True, None
        
    except Exception as e:
        error_msg = f"Startup validation failed: {e}"
        logging.error(error_msg)
        return False, error_msg


def main():
    """Main application entry point with optimized startup"""
    # Setup logging first
    setup_logging()
    setup_app_logging()
    
    # Set Qt attributes before creating QApplication
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    except AttributeError:
        pass
    
    # Create QApplication instance with optimizations
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Web Scraper Email Automation")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("WebScraperApp")
    app.setApplicationDisplayName("Web Scraper Email Automation Tool")
    
    # Performance optimizations (PyQt6 compatible)
    try:
        # Only set attributes that are available in PyQt6
        app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    except AttributeError:
        pass
    
    # Set application icon (if available)
    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass  # Icon file not found, continue without it
    
    # Apply performance optimizations early
    setup_performance_optimizations(app)
    
    # Show splash screen for better user experience
    splash = None
    try:
        from ui.splash_screen import SplashScreen
        splash = SplashScreen()
        splash.show()
        app.processEvents()
        splash.update_progress(10, "Applying performance optimizations...")
        app.processEvents()
    except Exception as e:
        logging.warning(f"Could not show splash screen: {e}")
    
    try:
        # Update splash screen progress
        if splash:
            splash.update_progress(20, "Performing startup validation...")
            app.processEvents()
        
        # Perform startup validation
        logging.info("Performing startup validation...")
        
        # Run async startup validation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            validation_success, validation_error = loop.run_until_complete(perform_startup_validation())
        finally:
            loop.close()
        
        if splash:
            splash.update_progress(40, "Validation complete...")
            app.processEvents()
        
        if not validation_success:
            # Hide splash before showing warning
            if splash:
                splash.hide()
            
            # Show warning but allow application to continue
            reply = QMessageBox.warning(
                None, 
                "Startup Validation Warning", 
                f"Some components failed validation:\n\n{validation_error}\n\n"
                "The application may not function properly. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                logging.info("User chose to exit due to validation failures")
                sys.exit(1)
            else:
                logging.warning("User chose to continue despite validation failures")
        
        # Update splash screen progress
        if splash:
            splash.update_progress(60, "Creating application controller...")
            app.processEvents()
        
        # Create application controller
        controller = ApplicationController()
        
        if splash:
            splash.update_progress(70, "Initializing user interface...")
            app.processEvents()
        
        # Create main window and connect to controller
        main_window = MainWindow()
        
        if splash:
            splash.update_progress(80, "Connecting components...")
            app.processEvents()
        
        # Set controller in main window (this will connect the signals)
        main_window.set_controller(controller)
        
        # Connect main window signals to controller
        main_window.status_message.connect(controller.status_update.emit)
        
        if splash:
            splash.update_progress(90, "Initializing core modules...")
            app.processEvents()
        
        # Initialize core modules
        controller.initialize_modules()
        
        if splash:
            splash.update_progress(100, "Ready!")
            app.processEvents()
            # Keep splash visible for a moment
            import time
            time.sleep(0.5)
            splash.hide()
        
        # Show main window
        main_window.show()
        
        # Setup cleanup on application exit
        app.aboutToQuit.connect(controller.cleanup)
        
        # Setup resource manager cleanup
        resource_manager = get_resource_manager()
        app.aboutToQuit.connect(resource_manager.cleanup_all_resources)
        
        logging.info("Application started successfully")
        
        # Start the event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"Application startup failed: {e}")
        QMessageBox.critical(None, "Startup Error", f"Failed to start application:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()