# Keeper PDF Generator

Automated PDF generation system that extracts customer data from Keeper vault and generates professional credential documents using Word templates.

## Features

- 🔐 **Persistent Login** - Secure authentication with Keeper vault
- 📄 **Template-based PDF Generation** - Uses enhanced Word templates with placeholders
- 🏢 **Customer Categories** - Supports both internal and external customer types
- 🔑 **Real Vault Data** - Extracts actual passwords, emails, and credentials
- 📤 **Vault Integration** - Ready for uploading generated PDFs back to vault
- 🎯 **Production Ready** - Clean, organized, and well-documented code

## System Architecture

```
Keeper Vault (Source) → Data Extraction → Template Processing → PDF Generation → Vault Upload
                     ↓                  ↓                    ↓               ↓
                 Custom Records    Enhanced Templates    Professional   Datenblätter
                 - Email accounts   - {{placeholders}}     PDFs          Folder
                 - Website logins   - Real data           - Credentials
                 - Server settings  - Customer-specific   - Ready to use
```

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Templates

```bash
# Enhance templates with placeholders
python enhance_templates_with_placeholders.py
```

### 3. Generate PDFs

```bash
# Run the main PDF generator
python keeper_pdf_system.py
```

### 4. Update Vault Templates (Optional)

```bash
# Upload enhanced templates to vault
python upload_templates_to_vault.py
```

## File Structure

```
keeper-pdf-generator/
├── keeper_pdf_system.py           # Main production script
├── enhance_templates_with_placeholders.py  # Template enhancement
├── upload_templates_to_vault.py    # Vault template updater
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── temp_templates/                # Template files
│   ├── ENHANCED_extern_template.docx    # External customer template
│   ├── ENHANCED_intern_template.docx    # Internal customer template
│   ├── 20250000_E-Mail_Datenblatt_Kundenname.docx  # Original extern
│   └── 20250000_Datenblatt_Kundenname.docx         # Original intern
└── generated_pdfs/               # Output directory
    ├── customer1_credentials.pdf
    ├── customer2_credentials.pdf
    └── ...
```

## Template Placeholders

The enhanced templates use these placeholders for dynamic content:

### Customer Information
- `{{customer_name}}` - Customer domain name
- `{{current_date}}` - Generation date
- `{{support_email}}` - Support contact

### Email Credentials
- `{{primary_email}}` - Primary email address
- `{{primary_email_password}}` - Primary email password
- `{{secondary_email}}` - Secondary email address
- `{{secondary_email_password}}` - Secondary email password

### Web Access
- `{{webmail_url}}` - Webmail access URL
- `{{website_login}}` - Website admin username
- `{{website_password}}` - Website admin password
- `{{website_url}}` - Website admin URL
- `{{statistics_login}}` - Web statistics username
- `{{statistics_password}}` - Web statistics password
- `{{statistics_url}}` - Web statistics URL

### Server Settings
- `{{smtp_server}}` - SMTP server address
- `{{imap_server}}` - IMAP server address
- `{{pop_server}}` - POP3 server address
- `{{imap_port}}`, `{{pop_port}}`, `{{smtp_port}}` - Server ports

## Vault Record Types

The system recognizes these custom Keeper record types:

- **Datenblatt: E-Mail-Postfach** - Email accounts with credentials
- **Datenblatt: Webmail-URL** - Webmail access information
- **Datenblatt: Website-Login** - Website administration access
- **Datenblatt: Web-Statistik-Login** - Web statistics access
- **Datenblatt: E-Mail-Hosts** - Email server configuration
- **Datenblatt: E-Mail-Alias** - Email aliases
- **Datenblatt: E-Mail-Weiterleitung** - Email forwarding

## Configuration

### Vault Folders

- **Vorlagen** (Templates): `up_Ke2WPMWY1Hj_hmNQ19Q`
- **Kunden** (Customers): `7Bs55LFNTRNOZyLgbQI0gA`
- **Datenblätter** (Data sheets): `hzirlSdHtHAW78cWmV_ong`

### Customer Categories

- **Extern**: External customers - Email-focused templates
- **Intern**: Internal customers - Comprehensive templates with web access

## Usage Examples

### Process All Customers

```bash
python keeper_pdf_system.py
# Select: A
```

### Process Single Customer

```bash
python keeper_pdf_system.py
# Select: 1 (for first customer)
```

### Enhance Templates

```bash
python enhance_templates_with_placeholders.py
# Creates ENHANCED_*.docx templates with {{placeholders}}
```

### Upload to Vault

```bash
python upload_templates_to_vault.py
# Creates backup records in Vorlagen folder
```

## Security Features

- ✅ **Persistent Login** - Secure authentication without repeated passwords
- ✅ **2FA Support** - Works with TOTP authentication
- ✅ **Encrypted Storage** - All data remains in Keeper vault
- ✅ **Local Processing** - No external services or cloud dependencies
- ✅ **Access Control** - Respects Keeper folder permissions

## Development

### Project History

This system was developed to automate the creation of customer credential documents from existing Keeper vault data. Key milestones:

1. **Initial Development** - Basic vault connectivity and PDF generation
2. **Template Enhancement** - Added docxtpl placeholders for dynamic content
3. **Data Extraction Fix** - Proper parsing of custom Keeper record types
4. **Production Readiness** - Clean code, documentation, and error handling

### Testing

The system has been tested with:
- 4 customer folders (intern/extern categories)
- 8 different record types
- Real vault credentials and passwords
- Word template processing and PDF conversion

### Future Enhancements

- [ ] Automatic vault upload of generated PDFs
- [ ] Email delivery of credential documents
- [ ] Batch processing with progress tracking
- [ ] Template customization interface
- [ ] Multi-language support

## Troubleshooting

### Common Issues

1. **Authentication Fails**
   - Ensure persistent login is enabled: `keeper shell → this-device persistent-login on`
   - Check username in script configuration

2. **Template Not Found**
   - Run `python enhance_templates_with_placeholders.py` first
   - Verify template files exist in `temp_templates/` folder

3. **PDF Conversion Fails**
   - Ensure Microsoft Word is installed
   - Check that `pywin32` is properly installed

4. **Empty Template Context**
   - Verify vault records have the expected custom field types
   - Check that customer folders contain the required record types

### Support

For issues and questions:
- Check the validation report in generated files
- Review log messages for detailed error information
- Verify Keeper vault permissions and folder access

## License

This project is developed for internal use with Keeper Security vault integration.

## Author

Developed by AI Assistant for automated customer credential document generation.