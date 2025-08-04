#!/usr/bin/env python3
"""
Keeper PDF System - Production-ready PDF generation from Keeper vault data

This system:
1. Connects to Keeper vault with persistent login
2. Extracts real customer data from custom record types
3. Generates professional PDFs using enhanced Word templates
4. Supports both intern and extern customer categories
5. Ready for vault upload integration

Requirements:
- keepercommander
- docxtpl
- python-docx
- pywin32 (for PDF conversion)

Usage:
    python keeper_pdf_system.py

Author: AI Assistant
Date: 2025
"""

import os
import logging
import tempfile
import win32com.client
from docxtpl import DocxTemplate
from keepercommander import api, params
from keepercommander.loginv3 import LoginV3Flow
from keepercommander.subfolder import try_resolve_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeeperPDFGenerator:
    """Main class for PDF generation from Keeper vault data"""
    
    def __init__(self, username='martin.test@kunze-medien.de'):
        self.username = username
        self.params = None
        self.template_paths = {
            'extern': 'temp_templates/ENHANCED_extern_template.docx',
            'intern': 'temp_templates/ENHANCED_intern_template.docx'
        }
    
    def authenticate(self):
        """Authenticate with Keeper using persistent login"""
        try:
            logger.info("Authenticating with Keeper...")
            self.params = params.KeeperParams()
            self.params.user = self.username
            
            flow = LoginV3Flow()
            flow.login(self.params)
            api.sync_down(self.params)
            
            logger.info("✅ Authentication successful")
            print(f"📊 Synced {len(self.params.record_cache)} records")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_customer_folders(self):
        """Get list of customer folders from vault"""
        try:
            customers = []
            
            # Known customer folder UIDs
            customer_folders = {
                'hoC-cSZloyT3rWmPHTRlpA': ('test-extern1.local (100000)', 'intern'),
                'W9LGwI-3uVeBaoYh6r-iEQ': ('test-extern2.local (200000)', 'extern'),
                'HkGCEGzahSpXb2cIwA4jNQ': ('test-extern3.local (300000)', 'intern'),
                'GK-qlciy45TBw_g6407gWw': ('test-extern4.local (400000)', 'extern')
            }
            
            for uid, (name, category) in customer_folders.items():
                if uid in self.params.folder_cache:
                    record_count = len(self.params.subfolder_record_cache.get(uid, []))
                    customers.append({
                        'name': name,
                        'uid': uid,
                        'category': category,
                        'record_count': record_count
                    })
            
            return customers
            
        except Exception as e:
            logger.error(f"Error getting customer folders: {e}")
            return []
    
    def extract_customer_data(self, customer_uid):
        """Extract customer data from vault records"""
        try:
            if customer_uid not in self.params.subfolder_record_cache:
                return []
            
            record_uids = self.params.subfolder_record_cache[customer_uid]
            records = []
            
            for record_uid in record_uids:
                try:
                    from keepercommander import vault
                    record = vault.KeeperRecord.load(self.params, record_uid)
                    if record:
                        record_data = self._extract_record_fields(record)
                        records.append(record_data)
                except Exception as e:
                    logger.warning(f"Error loading record {record_uid}: {e}")
            
            return records
            
        except Exception as e:
            logger.error(f"Error extracting customer data: {e}")
            return []
    
    def _extract_record_fields(self, record):
        """Extract fields from a single record"""
        data = {
            'title': record.title,
            'uid': record.record_uid,
            'type': 'unknown',
            'fields': {}
        }
        
        # Handle TypedRecord (custom types)
        if hasattr(record, 'type_name'):
            data['type'] = record.type_name
            data['notes'] = getattr(record, 'notes', '')
            
            # Extract custom fields
            if hasattr(record, 'custom'):
                for field in record.custom:
                    field_type = getattr(field, 'type', 'unknown')
                    field_value = getattr(field, 'value', '')
                    data['fields'][field_type] = str(field_value)
            
            # Extract standard fields
            if hasattr(record, 'fields'):
                for field in record.fields:
                    field_type = getattr(field, 'type', 'unknown')
                    field_value = getattr(field, 'value', '')
                    data['fields'][field_type] = str(field_value)
            
            # Standard password/login fields
            if hasattr(record, 'password'):
                data['password'] = record.password
            if hasattr(record, 'login'):
                data['login'] = record.login
        
        return data
    
    def _clean_field_value(self, value):
        """Clean field values from vault format"""
        if isinstance(value, str) and value.startswith("['") and value.endswith("']"):
            return value[2:-2]
        elif isinstance(value, list) and value:
            return str(value[0])
        return str(value) if value else ''
    
    def extract_vault_data(self, records):
        """Extract and organize vault data"""
        vault_data = {
            'emails': [],
            'webmail_url': '',
            'website_login': '',
            'website_password': '',
            'website_url': '',
            'statistics_login': '',
            'statistics_password': '',
            'statistics_url': '',
            'smtp_server': ''
        }
        
        for record in records:
            record_type = record.get('type', '')
            fields = record.get('fields', {})
            
            # Process different record types
            if 'E-Mail-Postfach' in record_type:
                email_data = {}
                for field_type, field_value in fields.items():
                    clean_val = self._clean_field_value(field_value)
                    if 'email' in field_type.lower() and clean_val:
                        email_data['email'] = clean_val
                    elif 'password' in field_type.lower() and clean_val:
                        email_data['password'] = clean_val
                
                if email_data.get('email'):
                    vault_data['emails'].append(email_data)
            
            elif 'Website-Login' in record_type:
                for field_type, field_value in fields.items():
                    clean_val = self._clean_field_value(field_value)
                    if 'login' in field_type.lower():
                        vault_data['website_login'] = clean_val
                    elif 'password' in field_type.lower():
                        vault_data['website_password'] = clean_val
                    elif 'url' in field_type.lower():
                        vault_data['website_url'] = clean_val
            
            elif 'Web-Statistik-Login' in record_type:
                for field_type, field_value in fields.items():
                    clean_val = self._clean_field_value(field_value)
                    if 'login' in field_type.lower():
                        vault_data['statistics_login'] = clean_val
                    elif 'password' in field_type.lower():
                        vault_data['statistics_password'] = clean_val
                    elif 'url' in field_type.lower():
                        vault_data['statistics_url'] = clean_val
            
            elif 'Webmail-URL' in record_type:
                for field_type, field_value in fields.items():
                    clean_val = self._clean_field_value(field_value)
                    if 'url' in field_type.lower():
                        vault_data['webmail_url'] = clean_val
        
        return vault_data
    
    def build_template_context(self, customer_name, vault_data):
        """Build context for template rendering"""
        customer_domain = customer_name.split('(')[0].strip().replace('.local', '')
        
        # Assign emails
        primary_email = ''
        primary_password = ''
        secondary_email = ''
        secondary_password = ''
        
        if vault_data['emails']:
            emails = sorted(vault_data['emails'], key=lambda x: x.get('email', ''))
            if len(emails) >= 1:
                primary_email = emails[0].get('email', '')
                primary_password = emails[0].get('password', '')
            if len(emails) >= 2:
                secondary_email = emails[1].get('email', '')
                secondary_password = emails[1].get('password', '')
        
        return {
            'customer_name': customer_domain,
            'current_date': '2025',
            'support_email': 'support@kunze-medien.de',
            'primary_email': primary_email,
            'primary_email_password': primary_password,
            'secondary_email': secondary_email,
            'secondary_email_password': secondary_password,
            'webmail_url': vault_data['webmail_url'],
            'website_login': vault_data['website_login'],
            'website_password': vault_data['website_password'],
            'website_url': vault_data['website_url'],
            'statistics_login': vault_data['statistics_login'],
            'statistics_password': vault_data['statistics_password'],
            'statistics_url': vault_data['statistics_url'],
            'smtp_server': vault_data['smtp_server'] or f"smtp.{customer_domain}.local",
            'imap_server': f"imap.{customer_domain}.local",
            'pop_server': f"pop.{customer_domain}.local",
            'imap_port': '993',
            'pop_port': '995',
            'smtp_port': '465'
        }
    
    def generate_pdf(self, template_path, context, customer_name, output_dir='generated_pdfs'):
        """Generate PDF from template and context"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Render template
            doc = DocxTemplate(template_path)
            doc.render(context)
            
            # Save DOCX
            safe_name = customer_name.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '_')
            temp_docx = os.path.join(output_dir, f"{safe_name}_credentials.docx")
            doc.save(temp_docx)
            
            # Convert to PDF
            pdf_path = temp_docx.replace('.docx', '.pdf')
            
            word_app = win32com.client.Dispatch('Word.Application')
            word_app.Visible = False
            word_doc = word_app.Documents.Open(os.path.abspath(temp_docx))
            word_doc.SaveAs2(os.path.abspath(pdf_path), FileFormat=17)
            word_doc.Close()
            word_app.Quit()
            
            logger.info(f"PDF generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return None
    
    def process_customer(self, customer):
        """Process a single customer"""
        logger.info(f"Processing customer: {customer['name']} ({customer['category']})")
        
        # Get template
        template_path = self.template_paths.get(customer['category'])
        if not template_path or not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return False
        
        # Extract data
        records = self.extract_customer_data(customer['uid'])
        if not records:
            logger.warning(f"No records found for customer: {customer['name']}")
            return False
        
        # Process data
        vault_data = self.extract_vault_data(records)
        context = self.build_template_context(customer['name'], vault_data)
        
        # Generate PDF
        pdf_path = self.generate_pdf(template_path, context, customer['name'])
        
        if pdf_path:
            logger.info(f"✅ Successfully processed: {customer['name']}")
            return True
        else:
            logger.error(f"❌ Failed to process: {customer['name']}")
            return False
    
    def run(self):
        """Main execution method"""
        print("🎯 KEEPER PDF GENERATOR")
        print("=" * 30)
        
        # Authenticate
        if not self.authenticate():
            return
        
        # Get customers
        customers = self.get_customer_folders()
        if not customers:
            print("❌ No customers found")
            return
        
        print(f"\n👥 Found {len(customers)} customers:")
        for i, customer in enumerate(customers, 1):
            print(f"   {i}. {customer['name']} ({customer['category']}) - {customer['record_count']} records")
        
        # Menu
        print(f"\nOptions:")
        print(f"   A = Process ALL customers")
        print(f"   1-{len(customers)} = Process specific customer")
        
        try:
            choice = input(f"\nSelect: ").strip().upper()
            
            if choice == 'A':
                success_count = 0
                for customer in customers:
                    if self.process_customer(customer):
                        success_count += 1
                
                print(f"\n📊 Batch processing complete: {success_count}/{len(customers)} successful")
                
            elif choice.isdigit() and 1 <= int(choice) <= len(customers):
                selected_customer = customers[int(choice) - 1]
                self.process_customer(selected_customer)
                
            else:
                print("❌ Invalid selection")
                
        except (ValueError, KeyboardInterrupt):
            print("❌ Cancelled")

def main():
    """Main entry point"""
    generator = KeeperPDFGenerator()
    generator.run()

if __name__ == "__main__":
    main()