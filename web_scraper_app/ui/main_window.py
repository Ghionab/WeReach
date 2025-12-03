"""
Main application window for the Web Scraper Email Automation Tool
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
    QLabel, QMenuBar, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from ui.styles import get_main_style, get_colors
# Removed status widgets - no longer needed, ProgressIndicator
from utils.state_manager import get_state_manager
from utils.keyboard_shortcuts import register_application_shortcuts, get_shortcut_manager


class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""
    
    # Signals for application-wide communication
    status_message = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.colors = get_colors()
        self.controller = None  # Will be set by main.py
        self.state_manager = get_state_manager()
        self.setup_ui()
        self.setup_menu_bar()
        # Removed status bar as requested - it was ugly
        self.setup_keyboard_shortcuts()
        self.setup_accessibility()
        self.setup_tooltips()
        
        # Register application-wide shortcuts using the shortcut manager
        register_application_shortcuts(self)
        self.setup_styles()
        self.connect_signals()
        self.restore_ui_state()
        self.setup_auto_save()
        
    def setup_ui(self):
        """Initialize the main UI components"""
        self.setWindowTitle("Web Scraper Email Automation Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(False)
        self.tab_widget.setDocumentMode(True)
        layout.addWidget(self.tab_widget)
        
        # Add placeholder tabs (will be replaced with actual tab widgets later)
        self.add_placeholder_tabs()
        
    def add_placeholder_tabs(self):
        """Add placeholder tabs for the main interface"""
        # Dashboard tab - import the actual dashboard tab
        from ui.dashboard_tab import DashboardTab
        self.dashboard_tab = DashboardTab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Email tab - import the actual email tab
        from ui.email_tab import EmailTab
        self.email_tab = EmailTab()
        self.tab_widget.addTab(self.email_tab, "Email")
        
        # History tab - import the actual history tab
        from ui.history_tab import HistoryTab
        self.history_tab = HistoryTab()
        self.tab_widget.addTab(self.history_tab, "History")
        
        # Settings tab - import the actual settings tab
        from ui.settings_tab import SettingsTab
        self.settings_tab = SettingsTab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
    def setup_menu_bar(self):
        """Setup the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Import URLs action
        import_action = QAction("&Import URLs from CSV", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("Import URLs from a CSV file")
        import_action.triggered.connect(self.import_urls)
        file_menu.addAction(import_action)
        
        # Export data action
        export_action = QAction("&Export Data to CSV", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export scraped data to CSV file")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Test connections action
        test_connections_action = QAction("&Test Connections", self)
        test_connections_action.setStatusTip("Test API and SMTP connections")
        test_connections_action.triggered.connect(self.test_connections)
        tools_menu.addAction(test_connections_action)
        
        # Clear data action
        clear_data_action = QAction("&Clear All Data", self)
        clear_data_action.setStatusTip("Clear all scraped and sent email data")
        clear_data_action.triggered.connect(self.clear_all_data)
        tools_menu.addAction(clear_data_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # Documentation action
        docs_action = QAction("&Documentation", self)
        docs_action.setShortcut("F1")
        docs_action.setStatusTip("Open application documentation")
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    # Removed status bar setup - it was ugly and unnecessary
        
    def setup_keyboard_shortcuts(self):
        """Setup comprehensive keyboard shortcuts for improved accessibility"""
        # Tab navigation shortcuts (Ctrl+1-4)
        for i in range(4):  # 4 tabs
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i+1}"), self)
            shortcut.activated.connect(lambda idx=i: self.tab_widget.setCurrentIndex(idx))
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Quick action shortcuts
        # Ctrl+R for refresh/scraping
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.quick_refresh)
        refresh_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Ctrl+G for generate emails
        generate_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        generate_shortcut.activated.connect(self.quick_generate_emails)
        generate_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Ctrl+Shift+S for send emails
        send_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        send_shortcut.activated.connect(self.quick_send_emails)
        send_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # F5 for refresh current tab
        f5_shortcut = QShortcut(QKeySequence("F5"), self)
        f5_shortcut.activated.connect(self.refresh_current_tab)
        f5_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Escape to stop current operation
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.stop_current_operation)
        escape_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Ctrl+T for test connections
        test_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        test_shortcut.activated.connect(self.test_connections)
        test_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Additional productivity shortcuts
        # Ctrl+N for new/add URL
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self.focus_url_input)
        new_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Ctrl+D for clear/delete
        clear_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        clear_shortcut.activated.connect(self.quick_clear_action)
        clear_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Ctrl+H for history
        history_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        history_shortcut.activated.connect(lambda: self.tab_widget.setCurrentIndex(2))
        history_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Alt+Left/Right for tab navigation
        prev_tab_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        prev_tab_shortcut.activated.connect(self.previous_tab)
        prev_tab_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        next_tab_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        next_tab_shortcut.activated.connect(self.next_tab)
        next_tab_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        
        # Ctrl+/ for help/shortcuts
        help_shortcut = QShortcut(QKeySequence("Ctrl+/"), self)
        help_shortcut.activated.connect(self.show_keyboard_shortcuts_help)
        help_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
    
    def setup_accessibility(self):
        """Setup comprehensive accessibility features"""
        # Set accessible names and descriptions
        self.setAccessibleName("Web Scraper Email Automation Tool")
        self.setAccessibleDescription(
            "Main application window for web scraping and email automation. "
            "Use Ctrl+1-4 to navigate tabs, Ctrl+/ for keyboard shortcuts help."
        )
        
        # Set tab widget accessibility
        self.tab_widget.setAccessibleName("Main Navigation Tabs")
        self.tab_widget.setAccessibleDescription(
            "Navigate between Dashboard, Email, History, and Settings. "
            "Use Ctrl+1-4 or Alt+Left/Right arrows to switch tabs."
        )
        
        # Set tab accessibility names with detailed descriptions
        tab_names = ["Dashboard", "Email Generation", "History", "Settings"]
        tab_descriptions = [
            "Web scraping and URL management. Add URLs manually or via CSV, start scraping operations.",
            "AI email generation and sending. Generate personalized emails and send to scraped contacts.",
            "Email history and tracking. View sent email statistics and search email history.",
            "Application configuration and settings. Configure API keys, SMTP settings, and test connections."
        ]
        
        for i, (name, desc) in enumerate(zip(tab_names, tab_descriptions)):
            if i < self.tab_widget.count():
                # PyQt6 doesn't have setTabAccessibleName/Description
                # Set accessible properties on the tab widget itself
                try:
                    self.tab_widget.setTabAccessibleName(i, name)
                    self.tab_widget.setTabAccessibleDescription(i, desc)
                except AttributeError:
                    # These methods don't exist in PyQt6, skip them
                    pass
        
        # Enable focus policy for keyboard navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.tab_widget.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        
        # Status bar accessibility removed - no longer needed
        
        # Set up menu bar accessibility
        menubar = self.menuBar()
        menubar.setAccessibleName("Main Menu Bar")
        menubar.setAccessibleDescription(
            "Application menu bar. Use Alt key to access menus, "
            "or use keyboard shortcuts for quick actions."
        )
        
        # Enable high contrast support
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        # Set window role for screen readers
        self.setWindowRole("MainWindow")
    
    def setup_tooltips(self):
        """Setup comprehensive tooltips for user guidance"""
        # Tab tooltips with keyboard shortcuts
        self.tab_widget.setTabToolTip(0, 
            "Dashboard - Add URLs and start scraping\n"
            "Shortcuts: Ctrl+1 (switch), Ctrl+N (add URL), Ctrl+R (start scraping)")
        self.tab_widget.setTabToolTip(1, 
            "Email - Generate and send AI-powered emails\n"
            "Shortcuts: Ctrl+2 (switch), Ctrl+G (generate), Ctrl+Shift+S (send)")
        self.tab_widget.setTabToolTip(2, 
            "History - View sent email history and statistics\n"
            "Shortcuts: Ctrl+3 (switch), Ctrl+H (quick access), F5 (refresh)")
        self.tab_widget.setTabToolTip(3, 
            "Settings - Configure API keys and SMTP settings\n"
            "Shortcuts: Ctrl+4 (switch), Ctrl+T (test connections)")
        
        # Status bar tooltips are handled by the individual widgets
        
        # Menu bar tooltips
        menubar = self.menuBar()
        for action in menubar.actions():
            menu = action.menu()
            if menu:
                if menu.title() == "&File":
                    menu.setToolTip("File operations - Import/Export data, Exit application")
                elif menu.title() == "&Tools":
                    menu.setToolTip("Application tools - Test connections, Clear data")
                elif menu.title() == "&Help":
                    menu.setToolTip("Help and documentation - Shortcuts (Ctrl+/), About")
    
    def setup_auto_save(self):
        """Setup automatic state saving"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_state)
        self.auto_save_timer.start(300000)  # Auto-save every 5 minutes
    
    def setup_styles(self):
        """Apply custom QSS styling"""
        self.setStyleSheet(get_main_style())
        
    def connect_signals(self):
        """Connect internal signals"""
        self.status_message.connect(self.update_status_message)
        self.progress_update.connect(self.update_progress)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def set_controller(self, controller):
        """Set the application controller and connect additional signals"""
        self.controller = controller
        
        # Connect controller signals to UI updates
        if self.controller:
            self.controller.status_update.connect(self.update_status_message)
            self.controller.connection_status_changed.connect(self.update_connection_status)
            self.controller.error_occurred.connect(self.show_error_message)
            
            # Connect dashboard tab signals to controller
            if hasattr(self, 'dashboard_tab'):
                self.connect_dashboard_signals()
            
            # Connect email tab signals to controller
            if hasattr(self, 'email_tab'):
                self.connect_email_signals()
            
            # Connect history tab signals to controller
            if hasattr(self, 'history_tab'):
                self.connect_history_signals()
            
            # Connect settings tab signals to controller
            if hasattr(self, 'settings_tab'):
                self.connect_settings_signals()
    
    def show_error_message(self, message):
        """Show error message to user"""
        QMessageBox.critical(self, "Error", message)
    
    def on_tab_changed(self, index):
        """Handle tab change events"""
        tab_names = ["Dashboard", "Email Generation", "History", "Settings"]
        if 0 <= index < len(tab_names):
            self.status_message.emit(f"Switched to {tab_names[index]} tab")
            
            # Refresh scraped emails when switching to Email Generation tab
            if index == 1 and hasattr(self, 'email_tab') and hasattr(self, 'controller') and self.controller:  # Email Generation tab
                try:
                    emails = self.controller.get_scraped_emails()
                    self.email_tab.update_scraped_emails(emails)
                except Exception as e:
                    print(f"Error refreshing scraped emails: {e}")
            
            # Update UI state
            self.state_manager.update_ui_state(tab_index=index)
    
    def update_status_message(self, message):
        """Update status message - now just logs it since status bar is removed"""
        # Status bar removed - just log the message
        print(f"Status: {message}")
        
    def update_progress(self, value):
        """Update progress indication (placeholder for future use)"""
        # This will be used by the controller for progress updates
        pass
    
    def update_connection_status(self, connected=False):
        """Update connection status indicator"""
        # Connection status widget removed - no longer needed
    
    # Menu action handlers
    def import_urls(self):
        """Handle import URLs action"""
        # Switch to Dashboard tab
        self.tab_widget.setCurrentIndex(0)
        self.status_message.emit("Switched to Dashboard tab for URL import")
        
    def export_data(self):
        """Handle export data action"""
        if not self.controller:
            self.show_error_message("Application controller not available")
            return
            
        from PyQt6.QtWidgets import QFileDialog
        
        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scraped Emails",
            "scraped_emails.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            success = self.controller.export_scraped_emails_csv(file_path)
            if success:
                QMessageBox.information(self, "Export Successful", f"Data exported to:\n{file_path}")
        
    def test_connections(self):
        """Handle test connections action"""
        if not self.controller:
            self.show_error_message("Application controller not available")
            return
            
        # Test both connections
        gemini_ok = self.controller.test_gemini_connection()
        smtp_ok = self.controller.test_smtp_connection()
        
        if gemini_ok and smtp_ok:
            QMessageBox.information(self, "Connection Test", "All connections are working properly!")
        else:
            message = "Connection test results:\n"
            message += f"• Gemini AI: {'Connected' if gemini_ok else 'Failed'}\n"
            message += f"• SMTP: {'Connected' if smtp_ok else 'Failed'}\n\n"
            message += "Check your settings in the Settings tab."
            QMessageBox.warning(self, "Connection Test", message)
        
    def clear_all_data(self):
        """Handle clear all data action"""
        reply = QMessageBox.question(
            self,
            "Clear All Data",
            "Are you sure you want to clear all scraped emails and sent email history?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.controller:
                self.controller.clear_all_data()
            else:
                self.show_error_message("Application controller not available")
    
    def show_documentation(self):
        """Show comprehensive documentation dialog"""
        from ui.help_system import show_help_dialog
        show_help_dialog(self)
    
    def connect_dashboard_signals(self):
        """Connect dashboard tab signals to controller"""
        # Connect scraping signals
        self.dashboard_tab.start_scraping_requested.connect(self.controller.start_scraping)
        self.dashboard_tab.start_crawling_requested.connect(self.controller.start_crawling)
        self.dashboard_tab.export_results_requested.connect(self.controller.export_scraped_emails_csv)
        self.dashboard_tab.export_filtered_requested.connect(self.handle_filtered_export)
        
        # Connect stop scraping button
        self.dashboard_tab.stop_scraping_btn.clicked.connect(self.controller.stop_scraping)
        
        # Connect controller signals to dashboard updates
        self.controller.scraping_started.connect(self.dashboard_tab.on_scraping_started)
        self.controller.scraping_finished.connect(self.dashboard_tab.on_scraping_finished)
        self.controller.scraping_progress.connect(self.dashboard_tab.on_scraping_progress)
        self.controller.email_found.connect(self.dashboard_tab.on_email_found)
        
        # Connect crawling signals (reuse scraping handlers)
        self.controller.crawling_started.connect(self.dashboard_tab.on_scraping_started)
        self.controller.crawling_finished.connect(self.dashboard_tab.on_scraping_completed)
        self.controller.crawling_progress.connect(self.dashboard_tab.on_scraping_progress)
        self.controller.error_occurred.connect(self.dashboard_tab.on_scraping_error)
        
        # Connect data updates for real-time email display
        self.controller.data_updated.connect(self.on_data_updated)
    
    def connect_email_signals(self):
        """Connect email tab signals to controller"""
        # Connect email generation signals
        self.email_tab.generate_emails_requested.connect(self.controller.generate_emails)
        self.email_tab.generate_emails_for_selection_requested.connect(self.controller.generate_emails_for_selection)
        self.email_tab.send_emails_requested.connect(self.controller.send_emails)
        
        # Connect controller signals to email tab updates
        self.controller.email_generation_started.connect(self.email_tab.on_generation_started)
        self.controller.email_generation_finished.connect(self.email_tab.on_emails_generated)
        self.controller.email_generation_progress.connect(self.email_tab.on_generation_progress)
        
        self.controller.email_sending_started.connect(self.email_tab.on_sending_started)
        self.controller.email_sending_finished.connect(self.email_tab.on_emails_sent)
        self.controller.email_sending_progress.connect(self.email_tab.on_sending_progress)
        
        # Connect error handling
        self.controller.error_occurred.connect(self.email_tab.on_generation_error)
        self.controller.error_occurred.connect(self.email_tab.on_sending_error)
        
        # Update email tab with scraped emails when data changes
        self.controller.data_updated.connect(self.update_email_tab_data)
        
        # Initialize email tab with existing scraped emails
        try:
            existing_emails = self.controller.get_scraped_emails()
            if existing_emails:
                self.email_tab.update_scraped_emails(existing_emails)
        except Exception as e:
            print(f"Failed to load existing emails: {e}")
    
    def on_data_updated(self, data_type: str):
        """Handle data updates from controller"""
        if data_type == "scraped_emails" and hasattr(self, 'dashboard_tab'):
            # Update dashboard with new scraped emails
            emails = self.controller.get_scraped_emails()
            # This will be handled by the dashboard tab's update methods
            pass
    
    def handle_filtered_export(self, filter_options: dict):
        """Handle filtered export request from dashboard"""
        if not self.controller:
            self.show_error_message("Application controller not available")
            return
        
        # Extract filter options
        date_range = filter_options.get('date_range')
        website_filter = filter_options.get('website_filter')
        
        # Start filtered export
        success = self.controller.export_filtered_emails(date_range, website_filter)
        if not success:
            self.show_error_message("Failed to start filtered export")
    
    def update_email_tab_data(self, data_type: str):
        """Update email tab with new data"""
        if data_type == "scraped_emails" and hasattr(self, 'email_tab'):
            emails = self.controller.get_scraped_emails()
            self.email_tab.update_scraped_emails(emails)
    
    def connect_history_signals(self):
        """Connect history tab signals to controller"""
        # Connect history refresh signal
        self.history_tab.refresh_requested.connect(self.controller.refresh_email_history)
        self.history_tab.export_history_requested.connect(self.controller.export_sent_email_history)
        
        # Connect controller signals to history tab updates
        self.controller.email_history_updated.connect(self.history_tab.update_email_history)
        
        # Update history tab when emails are sent
        self.controller.email_sending_finished.connect(self.refresh_history_data)
        
        # Load initial history data
        self.controller.refresh_email_history()
    
    def refresh_history_data(self):
        """Refresh history data after email operations"""
        if hasattr(self, 'history_tab') and self.controller:
            self.controller.refresh_email_history()
    
    def connect_settings_signals(self):
        """Connect settings tab signals to controller"""
        # Connect configuration change signal
        self.settings_tab.configuration_changed.connect(self.on_configuration_changed)
        
        # Update connection status when configuration changes
        self.settings_tab.configuration_changed.connect(self.update_connection_status_from_config)
    
    def on_configuration_changed(self):
        """Handle configuration changes from settings tab"""
        if self.controller:
            # Configuration changed - no need to reload since it's handled by config manager
            print("Configuration updated successfully")
        
        # Update connection status
        self.update_connection_status_from_config()
    
    def update_connection_status_from_config(self):
        """Update connection status based on current configuration"""
        if hasattr(self, 'settings_tab'):
            status = self.settings_tab.config_manager.get_configuration_status()
            self.update_connection_status(status["fully_configured"])
    
    # Quick action methods for keyboard shortcuts
    def quick_refresh(self):
        """Quick refresh action - context-dependent"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Dashboard
            # Trigger smart crawl if URLs are available
            if hasattr(self, 'dashboard_tab') and self.dashboard_tab.url_list_widget.rowCount() > 0:
                self.dashboard_tab.start_crawling()
            else:
                self.status_message.emit("Add URLs first, then use Ctrl+R to start Smart Crawl")
        elif current_tab == 1:  # Email
            self.status_message.emit("Use 'Generate Emails' button to create emails")
        elif current_tab == 2:  # History
            if hasattr(self, 'history_tab'):
                self.history_tab.refresh_history()
            self.status_message.emit("Email history refreshed")
        elif current_tab == 3:  # Settings
            self.status_message.emit("Test connections in Settings tab")
    
    def quick_generate_emails(self):
        """Quick generate emails action"""
        # Switch to email tab
        self.tab_widget.setCurrentIndex(1)
        self.status_message.emit("Switched to Email tab - Use 'Generate Emails' button")
    
    def quick_send_emails(self):
        """Quick send emails action"""
        # Switch to email tab
        self.tab_widget.setCurrentIndex(1)
        self.status_message.emit("Switched to Email tab - Use 'Send Emails' button")
    
    def refresh_current_tab(self):
        """Refresh current tab content"""
        current_tab = self.tab_widget.currentIndex()
        tab_names = ["Dashboard", "Email", "History", "Settings"]
        
        if current_tab == 2 and hasattr(self, 'history_tab'):  # History tab
            self.history_tab.refresh_history()
            self.status_message.emit("History tab refreshed")
        else:
            tab_name = tab_names[current_tab] if current_tab < len(tab_names) else "Unknown"
            self.status_message.emit(f"{tab_name} tab refreshed")
    
    def stop_current_operation(self):
        """Stop any running operations"""
        if self.controller:
            # Stop scraping if running
            if self.controller.is_scraping:
                self.controller.stop_scraping()
                self.status_message.emit("Scraping operation stopped")
                return
            
            # Check for other running operations
            if self.controller.is_generating_emails:
                self.status_message.emit("Email generation is running - cannot stop")
                return
            
            if self.controller.is_sending_emails:
                self.status_message.emit("Email sending is running - cannot stop")
                return
        
        self.status_message.emit("No operations to stop")
    
    def focus_url_input(self):
        """Focus on URL input field in Dashboard tab"""
        # Switch to Dashboard tab
        self.tab_widget.setCurrentIndex(0)
        
        # Focus on URL input if available
        if hasattr(self, 'dashboard_tab') and hasattr(self.dashboard_tab, 'url_input'):
            self.dashboard_tab.url_input.setFocus()
            self.dashboard_tab.url_input.selectAll()
            self.status_message.emit("Ready to add new URL")
    
    def quick_clear_action(self):
        """Context-dependent clear action"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Dashboard
            if hasattr(self, 'dashboard_tab'):
                # Clear URL input if it has focus, otherwise clear results
                if self.dashboard_tab.url_input.hasFocus():
                    self.dashboard_tab.url_input.clear()
                    self.status_message.emit("URL input cleared")
                else:
                    self.dashboard_tab.clear_results()
                    self.status_message.emit("Scraping results cleared")
        elif current_tab == 1:  # Email
            if hasattr(self, 'email_tab'):
                self.email_tab.select_no_emails()
                self.status_message.emit("Email selection cleared")
        elif current_tab == 2:  # History
            if hasattr(self, 'history_tab'):
                self.history_tab.clear_filters()
                self.status_message.emit("History filters cleared")
        elif current_tab == 3:  # Settings
            self.status_message.emit("Use individual clear buttons in Settings")
    
    def previous_tab(self):
        """Navigate to previous tab"""
        current = self.tab_widget.currentIndex()
        previous = (current - 1) % self.tab_widget.count()
        self.tab_widget.setCurrentIndex(previous)
    
    def next_tab(self):
        """Navigate to next tab"""
        current = self.tab_widget.currentIndex()
        next_tab = (current + 1) % self.tab_widget.count()
        self.tab_widget.setCurrentIndex(next_tab)
    
    def show_keyboard_shortcuts_help(self):
        """Show keyboard shortcuts help dialog using the shortcut manager"""
        shortcut_manager = get_shortcut_manager()
        shortcut_manager.show_help_dialog(self)
    
    def auto_save_state(self):
        """Automatically save application state"""
        try:
            self.save_ui_state()
            if self.controller:
                self.controller.save_application_state()
            # Don't show message for auto-save to avoid spam
        except Exception as e:
            # Silently handle auto-save errors
            pass
    
    def restore_ui_state(self):
        """Restore UI state from state manager"""
        try:
            ui_state = self.state_manager.get_ui_state()
            
            # Restore active tab
            active_tab = ui_state.get("active_tab", 0)
            if 0 <= active_tab < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(active_tab)
            
            # Restore window geometry
            geometry = ui_state.get("window_geometry")
            if geometry:
                # Note: In a real implementation, you'd use QByteArray.fromBase64()
                # For now, we'll just log that geometry restoration is available
                pass
            
            # Restore window state
            window_state = ui_state.get("window_state")
            if window_state:
                # Note: In a real implementation, you'd use QByteArray.fromBase64()
                # For now, we'll just log that window state restoration is available
                pass
                
        except Exception as e:
            # Don't fail if state restoration fails
            pass
    
    def save_ui_state(self):
        """Save current UI state to state manager"""
        try:
            # Save current tab
            current_tab = self.tab_widget.currentIndex()
            
            # Save window geometry and state
            # Note: In a real implementation, you'd use saveGeometry().toBase64().data().decode()
            geometry = None  # self.saveGeometry().toBase64().data().decode()
            window_state = None  # self.saveState().toBase64().data().decode()
            
            self.state_manager.update_ui_state(
                tab_index=current_tab,
                geometry=geometry,
                window_state=window_state
            )
            
        except Exception as e:
            # Don't fail if state saving fails
            pass
    
    def show_about(self):
        """Show about dialog"""
        # Get application statistics for about dialog
        stats = self.state_manager.get_statistics()
        session_info = self.state_manager.get_session_info()
        
        stats_text = f"""
        <p><b>Session Statistics:</b></p>
        <ul>
        <li>Session Count: {session_info.get('session_count', 0)}</li>
        <li>Emails Scraped: {stats.get('total_emails_scraped', 0)}</li>
        <li>Emails Sent: {stats.get('total_emails_sent', 0)}</li>
        <li>Websites Scraped: {stats.get('total_websites_scraped', 0)}</li>
        </ul>
        """
        
        QMessageBox.about(
            self, 
            "About Web Scraper Email Automation Tool", 
            "<h3>Web Scraper Email Automation Tool v1.0.0</h3>"
            "<p>A professional desktop application for web scraping and automated email campaigns.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Real-time web scraping with progress tracking</li>"
            "<li>AI-powered email generation using Gemini AI</li>"
            "<li>Automated SMTP email sending</li>"
            "<li>Comprehensive email history tracking</li>"
            "<li>CSV import/export functionality</li>"
            "</ul>"
            f"{stats_text}"
            "<p><b>Built with:</b> PyQt6, Playwright, BeautifulSoup4, Google Generative AI</p>"
            "<p>© 2024 Web Scraper Email Automation Tool</p>"
        )
    
    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?\n\nAny running operations will be stopped.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Save UI state before closing
            self.save_ui_state()
            
            # Emit signal to stop any running operations
            self.status_message.emit("Application closing...")
            event.accept()
        else:
            event.ignore()