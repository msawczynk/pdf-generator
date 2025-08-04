#!/usr/bin/env python3
"""
Upload Enhanced Templates to Vault - Replace templates in Vorlagen folder with enhanced versions
"""

import os
from keepercommander import api, params, vault
from keepercommander.loginv3 import LoginV3Flow
from keepercommander.commands import record_edit

def authenticate():
    """Authenticate with persistent login"""
    print("🔐 Authenticating with Keeper...")
    keeper_params = params.KeeperParams()
    keeper_params.user = 'martin.test@kunze-medien.de'
    
    flow = LoginV3Flow()
    flow.login(keeper_params)
    api.sync_down(keeper_params)
    
    print("✅ Authenticated successfully")
    return keeper_params

def upload_enhanced_template_to_vault(params, local_template_path, vault_record_uid, template_name):
    """Upload enhanced template to replace existing template in vault"""
    
    try:
        print(f"📤 Uploading enhanced template: {template_name}")
        print(f"   Local file: {local_template_path}")
        print(f"   Vault record UID: {vault_record_uid}")
        
        if not os.path.exists(local_template_path):
            print(f"❌ Enhanced template not found: {local_template_path}")
            return False
        
        # Read the enhanced template file
        with open(local_template_path, 'rb') as f:
            template_data = f.read()
        
        print(f"   📄 Template size: {len(template_data)} bytes")
        
        # For now, create a backup record instead of replacing the original
        # This is safer for testing
        backup_title = f"{template_name}_Enhanced_Backup"
        
        print(f"🔧 Creating backup record: {backup_title}")
        
        # Create new record for enhanced template
        add_cmd = record_edit.RecordAddCommand()
        
        # Target Vorlagen folder
        vorlagen_uid = "up_Ke2WPMWY1Hj_hmNQ19Q"
        
        try:
            record_uid = add_cmd.execute(
                params,
                title=backup_title,
                folder=vorlagen_uid,
                notes=f"Enhanced template with docxtpl placeholders\n\nOriginal: {template_name}\nEnhanced: {os.path.basename(local_template_path)}\n\nContains placeholders:\n- {{{{primary_email}}}}\n- {{{{primary_email_password}}}}\n- {{{{webmail_url}}}}\n- {{{{smtp_server}}}}\n- {{{{customer_name}}}}\n\nGenerated: 2025"
            )
            
            if record_uid:
                print(f"✅ Enhanced template record created: {record_uid}")
                print(f"📎 Template file ready for manual attachment")
                print(f"💡 Manually attach {os.path.basename(local_template_path)} to this record")
                return True
            else:
                print(f"❌ Failed to create template record")
                return False
                
        except Exception as e:
            print(f"❌ Error creating template record: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error uploading template: {e}")
        return False

def update_vault_templates():
    """Update templates in vault with enhanced versions"""
    
    print("🎯 UPDATING VAULT TEMPLATES")
    print("=" * 40)
    
    # Authenticate
    params = authenticate()
    
    # Template mappings
    templates_to_upload = [
        {
            'local_path': 'temp_templates/ENHANCED_extern_template.docx',
            'vault_uid': 'ngO8Tz-HuUiwtrieQ9c2IA',  # Vorlage Extern
            'name': 'Vorlage Extern'
        },
        {
            'local_path': 'temp_templates/ENHANCED_intern_template.docx',
            'vault_uid': 'RFjSeNwjkE4JySK1yfyHew',  # Vorlage Intern
            'name': 'Vorlage Intern'
        }
    ]
    
    success_count = 0
    
    for template_info in templates_to_upload:
        success = upload_enhanced_template_to_vault(
            params,
            template_info['local_path'],
            template_info['vault_uid'],
            template_info['name']
        )
        
        if success:
            success_count += 1
        
        print()  # Add spacing
    
    print(f"📊 VAULT TEMPLATE UPDATE SUMMARY:")
    print(f"   ✅ Successfully processed: {success_count}/{len(templates_to_upload)} templates")
    print(f"   📁 New records created in Vorlagen folder")
    print(f"   📎 Manual step: Attach enhanced .docx files to the new records")
    print(f"   🔄 After attachment, you can replace the original templates")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Go to Keeper vault → Vorlagen folder")
    print(f"   2. Find the new '_Enhanced_Backup' records")
    print(f"   3. Manually attach the enhanced .docx files")
    print(f"   4. Test the enhanced templates")
    print(f"   5. Replace original templates when satisfied")

def main():
    """Main function"""
    
    print("📤 VAULT TEMPLATE UPDATER")
    print("=" * 30)
    
    # Check if enhanced templates exist
    enhanced_templates = [
        'temp_templates/ENHANCED_extern_template.docx',
        'temp_templates/ENHANCED_intern_template.docx'
    ]
    
    missing_templates = []
    for template in enhanced_templates:
        if not os.path.exists(template):
            missing_templates.append(template)
    
    if missing_templates:
        print(f"❌ Missing enhanced templates:")
        for template in missing_templates:
            print(f"   {template}")
        print(f"\n💡 Run 'python enhance_templates_with_placeholders.py' first")
        return
    
    print(f"✅ Enhanced templates found:")
    for template in enhanced_templates:
        size = os.path.getsize(template)
        print(f"   {os.path.basename(template)} ({size} bytes)")
    
    # Confirm upload
    try:
        confirm = input(f"\n📤 Upload enhanced templates to vault? (y/N): ").strip().lower()
        
        if confirm == 'y':
            update_vault_templates()
        else:
            print("❌ Upload cancelled")
            
    except KeyboardInterrupt:
        print("\n❌ Cancelled")

if __name__ == "__main__":
    main()