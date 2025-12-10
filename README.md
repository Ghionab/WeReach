# Web Scraper Email Automation Tool

A professional desktop application for automated web scraping and AI-powered email campaigns. Built with PyQt6, this tool combines web scraping, AI email generation, and automated SMTP sending in a modern, user-friendly interface.

![Application Screenshot](docs/screenshot.png)

## 🚀 Features

### 🕷️ **Advanced Web Scraping**
- **Smart Crawling**: Deep crawl websites to discover internal pages and extract emails
- **Quick Scraping**: Fast single-page email extraction
- **Dual Engine Support**: Playwright for dynamic content + BeautifulSoup for static parsing
- **Real-time Progress**: Live progress tracking with detailed status updates
- **Robust Error Handling**: Automatic retries and fallback mechanisms

### 🤖 **AI-Powered Email Generation**
- **Gemini AI Integration**: Generate personalized cold emails using Google's Gemini AI
- **Context-Aware Content**: AI analyzes scraped website content for personalized messaging
- **Bulk Generation**: Create multiple emails simultaneously for different websites
- **Email Preview & Editing**: Review and customize generated emails before sending

### 📧 **Automated Email Sending**
- **SMTP Integration**: Support for Gmail, Outlook, and custom SMTP servers
- **Bulk Email Campaigns**: Send personalized emails to multiple recipients
- **Progress Tracking**: Real-time sending progress with success/failure reporting
- **Email History**: Complete audit trail of all sent emails

### 📊 **Data Management**
- **SQLite Database**: Persistent storage for scraped emails and sent history
- **CSV Import/Export**: Import URL lists and export scraped data
- **Advanced Filtering**: Filter emails by date, website, status
- **Search Functionality**: Quick search through email history

### 🎨 **Modern User Interface**
- **Professional Dark Theme**: Elegant gold and dark color scheme
- **Tabbed Interface**: Organized workflow with Dashboard, Email, History, and Settings tabs
- **Responsive Design**: Optimized for different screen sizes
- **Keyboard Shortcuts**: Comprehensive hotkey support for power users
- **Accessibility**: Screen reader compatible with proper ARIA labels

## 📋 Requirements

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space
- **Internet**: Required for AI services and email sending

### API Requirements
- **Gemini AI API Key**: For email generation (free tier available)
- **SMTP Credentials**: Gmail App Password or custom SMTP server

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/web-scraper-email-automation.git
cd web-scraper-email-automation
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
```bash
playwright install
```

### 5. Run the Application
```bash
python main.py
```

## ⚙️ Configuration

### 1. Gemini AI Setup
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. In the app, go to **Settings** tab
4. Enter your API key in the "Gemini AI Configuration" section
5. Click "Test Connection" to verify

### 2. Gmail SMTP Setup
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. In the app Settings tab, configure SMTP:
   - **Server**: smtp.gmail.com
   - **Port**: 587
   - **Email**: your-email@gmail.com
   - **Password**: Your 16-character App Password
   - **TLS**: Enabled

### 3. Custom SMTP Setup
For other email providers, configure the SMTP settings accordingly:
- **Outlook**: smtp-mail.outlook.com:587
- **Yahoo**: smtp.mail.yahoo.com:587
- **Custom**: Your provider's SMTP settings

## 📖 Usage Guide

### 🏠 Dashboard Tab
1. **Add URLs**: Enter website URLs to scrape (one per line or import from CSV)
2. **Choose Scraping Method**:
   - **Smart Crawl**: Deep crawl for maximum email discovery
   - **Quick Scrape**: Fast single-page scraping
3. **Monitor Progress**: Watch real-time scraping progress and results
4. **Export Results**: Save scraped emails to CSV

### ✉️ Email Tab
1. **Review Scraped Emails**: See all discovered emails organized by website
2. **Select Recipients**: Choose which emails to generate content for
3. **Generate Emails**: Use AI to create personalized cold emails
4. **Preview & Edit**: Review and customize generated content
5. **Send Campaign**: Send emails to selected recipients

### 📋 History Tab
1. **View Sent Emails**: Complete history of all email campaigns
2. **Search & Filter**: Find specific emails by recipient, subject, or date
3. **Export History**: Save email history to CSV for analysis
4. **Track Performance**: Monitor delivery success rates

### ⚙️ Settings Tab
1. **Configure APIs**: Set up Gemini AI and SMTP credentials
2. **Test Connections**: Verify all services are working
3. **Manage Data**: Clear cached data or reset application state

## 🎯 Keyboard Shortcuts

### Navigation
- **Ctrl+1-4**: Switch between tabs
- **Alt+Left/Right**: Navigate tabs
- **Ctrl+/**: Show keyboard shortcuts help

### Actions
- **Ctrl+R**: Start scraping/refresh current tab
- **Ctrl+G**: Generate emails
- **Ctrl+Shift+S**: Send emails
- **Ctrl+T**: Test connections
- **Ctrl+E**: Export data
- **Ctrl+I**: Import URLs
- **Escape**: Stop current operation

### Utility
- **Ctrl+N**: Focus URL input
- **Ctrl+D**: Context-dependent clear action
- **Ctrl+H**: Go to History tab
- **F5**: Refresh current tab
- **F1**: Show documentation

## 🏗️ Architecture

### Core Components
```
├── UI Layer (PyQt6)
│   ├── Main Window & Tabs
│   ├── Custom Styling (QSS)
│   └── Event Handling
├── Application Controller
│   ├── Business Logic
│   ├── Signal Coordination
│   └── State Management
├── Core Modules
│   ├── Web Scraper (Playwright + BeautifulSoup)
│   ├── AI Client (Gemini API)
│   ├── Email Sender (SMTP)
│   └── Database (SQLite)
└── Utilities
    ├── Validation & Error Handling
    ├── Logging & Monitoring
    └── Performance Optimization
```

### Data Flow
1. **Scraping**: URLs → Web Scraper → Email Models → Database
2. **Generation**: Email Models → AI Client → Generated Content → Database
3. **Sending**: Generated Content → SMTP Client → Delivery Status → Database
4. **Export**: Database → CSV Files

## 🔧 Development

### Project Structure
```
web_scraper_app/
├── core/           # Core business logic
├── ui/             # User interface components
├── models/         # Data models
├── utils/          # Utility functions
└── tests/          # Test files
```

### Key Technologies
- **PyQt6**: Modern desktop GUI framework
- **Playwright**: Web automation and scraping
- **BeautifulSoup4**: HTML parsing
- **Google Generative AI**: AI-powered email generation
- **SQLite**: Embedded database
- **aiosmtplib**: Asynchronous SMTP client

### Testing
```bash
# Run basic integration tests
python test_basic_integration.py

# Run end-to-end workflow test
python test_end_to_end_workflow.py

# Run UI styling test
python test_modern_ui.py
```

## 🐛 Troubleshooting

### Common Issues

#### "No emails found"
- Ensure websites have publicly visible email addresses
- Try Smart Crawl instead of Quick Scrape
- Check if the website blocks automated access

#### "Gemini AI connection failed"
- Verify your API key is correct
- Check internet connection
- Ensure you haven't exceeded API quotas

#### "SMTP authentication failed"
- For Gmail, use App Password, not regular password
- Verify 2FA is enabled on your account
- Check server settings and port numbers

#### "Application won't start"
- Ensure Python 3.8+ is installed
- Install all requirements: `pip install -r requirements.txt`
- Install Playwright browsers: `playwright install`

### Logs and Debugging
- Application logs are saved to `web_scraper_app.log`
- Enable debug mode by setting log level to DEBUG
- Check the console output for real-time error messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Documentation**: Check the built-in help system (F1)
- **Issues**: Report bugs on GitHub Issues
- **Email**: support@yourapp.com

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with full scraping and email automation
- Modern dark UI with gold accents
- Gemini AI integration for email generation
- Comprehensive SMTP support
- SQLite database with export functionality
- Advanced error handling and retry mechanisms

## 🙏 Acknowledgments

- **Google Gemini AI** for powerful email generation capabilities
- **Playwright Team** for excellent web automation tools
- **PyQt6** for the robust desktop GUI framework
- **BeautifulSoup** for reliable HTML parsing

---

**Built with ❤️ for email marketing professionals and developers**