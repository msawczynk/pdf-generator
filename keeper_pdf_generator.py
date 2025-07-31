import sys
import os
import argparse
import json
import csv
import datetime
from io import BytesIO  # For in-memory file handling
import logging
import getpass  # For secure password input
import re  # For placeholder substitution
import tempfile  # For temp files in PDF conversion

from docxtpl import DocxTemplate  # For filling Word templates
import win32com.client  # For DOCX to PDF conversion

from keepercommander import api, params, loginv3  # Keeper SDK imports (adjust path if needed)
from keepercommander.loginv3 import LoginV3Flow  # For v3 login flow
from keepercommander.subfolder import try_resolve_path  # For folder path resolution
from keepercommander.record_management import add_record_to_folder  # For adding records
from keepercommander.generator import generate  # For password generation
from keepercommander.proto import record_pb2  # For add record rq
from keepercommander import vault  # For KeeperRecord
from keepercommander.utils import generate_uid  # For new UIDs
from keepercommander.attachment import UploadTask, upload_attachments  # For uploading PDF
from keepercommander.commands.register import OneTimeShareCreateCommand  # For one-time shares
from keepercommander.recordv3 import RecordV3, add_record_v3  # For v3 records
from keepercommander.proto import enterprise_pb2  # For enterprise permissions
from keepercommander.utils import utils  # For base64_url_decode
from keepercommander.commands.base import FolderMixin  # For get_records_in_folder_tree
from keepercommander.proto import folder_pb2  # For FolderAddRequest

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Adjust sys.path to include cloned Commander repo if not installed
sys.path.append(os.path.join(os.path.dirname(__file__), 'Commander'))

PROMPTS = {
    'en': {
        'json_uid': 'Enter JSON template record UID: ',
        'word_uid': 'Enter Word template record UID: ',
        'source_folder': 'Enter source folder UID/path: ',
        'target_folder': 'Enter target folder UID/path: ',
        'name': 'Enter customer name: ',
        'email': 'Enter customer email (optional): ',
        'custom': 'Enter custom param (optional): ',
    },
    'de': {
        'json_uid': 'Geben Sie die UID des JSON-Vorlagenrecords ein: ',
        'word_uid': 'Geben Sie die UID des Word-Vorlagenrecords ein: ',
        'source_folder': 'Geben Sie UID/Pfad des Quellordners ein: ',
        'target_folder': 'Geben Sie UID/Pfad des Zielordners ein: ',
        'name': 'Geben Sie den Kundennamen ein: ',
        'email': 'Geben Sie die Kunden-E-Mail ein (optional): ',
        'custom': 'Geben Sie benutzerdefinierten Parameter ein (optional): ',
    }
}

def authenticate(params):
    """Authenticate with Keeper using persistent login and master password."""
    try:
        flow = LoginV3Flow()
        # Check for persistent login; if not, prompt for master password
        if not params.session_token:
            if not params.password:
                params.password = getpass.getpass(prompt='Enter Master Password: ', stream=None)
        flow.login(params)  # Handles persistent login, SSO, etc.
        logging.info('Authenticated successfully.')
    except Exception as e:
        logging.error(f'Authentication failed: {e}')
        sys.exit(1)

def get_user_input(prompt_key, validator=None, lang='en'):
    prompt = PROMPTS.get(lang, PROMPTS['en'])[prompt_key]
    while True:
        value = input(prompt).strip()
        if validator and not validator(value):
            logging.warning('Invalid input. Try again.' if lang == 'en' else 'Ungültige Eingabe. Versuchen Sie es erneut.')
            continue
        return value

def validate_record_uid(uid, params):
    """Validate if a record UID exists in the vault."""
    try:
        api.get_record(params, uid)
        return True
    except:
        return False

def validate_folder(path_or_uid, params):
    """Validate if a folder path or UID exists."""
    folder, _ = try_resolve_path(params, path_or_uid)
    return folder is not None

def download_json_template(params, uid):
    """Download JSON template from record notes."""
    rec = api.get_record(params, uid)
    if not rec.notes:
        raise ValueError('No JSON in record notes')
    return json.loads(rec.notes)

def download_word_template(params, uid):
    """Download Word template as in-memory stream."""
    rec = api.get_record(params, uid)
    if 'extra' not in rec or 'files' not in rec.extra or not rec.extra['files']:
        raise ValueError('No attachment in Word template record')
    file_info = rec.extra['files'][0]
    attachment_id = file_info['id']
    stream = BytesIO()
    api.download_attachment(params, uid, attachment_id, stream)
    stream.seek(0)
    return stream

def substitute_placeholders(template, customer):
    """Substitute ${var} in JSON template with customer data."""
    json_str = json.dumps(template)
    json_str = re.sub(r'\$\{customer_name\}', customer['name'], json_str)
    # Add more substitutions as needed
    return json.loads(json_str)

def create_folder(params, name, parent_uid=None):
    rq = folder_pb2.FolderAddRequest()
    rq.name = name
    if parent_uid:
        rq.parent_uid = utils.base64_url_decode(parent_uid)
    rs = api.communicate_rest(params, rq, 'folder/add_folder')  # Confirm endpoint
    return utils.base64_url_encode(rs.folder_uid)

def delete_folder(params, folder_uid):
    rq = folder_pb2.FolderDeleteRequest()
    rq.folder_uid = utils.base64_url_decode(folder_uid)
    api.communicate_rest(params, rq, 'folder/delete_folder')

def get_folder_records(params, folder_uid):
    record_uids = FolderMixin.get_records_in_folder_tree(params, folder_uid)
    records = {}
    for uid in record_uids:
        rec = vault.get_record(params, uid)  # Or v3 equivalent
        records[rec.title] = rec.to_dict()  # Assume to_dict method
    return records

def process_customer(params, customer, json_template, target_folder_uid):
    """Process one customer: create structure, autogenerate, etc."""
    template = substitute_placeholders(json_template, customer)
    root_folder_uid = create_folder(params, template['root_folder'], target_folder_uid)
    subfolder_uids = {}
    for sub in template.get('subfolders', []):
        sub_uid = create_folder(params, sub, root_folder_uid)
        subfolder_uids[sub] = sub_uid
    for rec_data in template.get('records', []):
        folder = rec_data['folder']
        folder_uid = subfolder_uids.get(folder, root_folder_uid)
        # Update record creation to v3
        record = RecordV3()
        record.title = rec_data['title']
        # For fields, use record.set_field etc. for v3 structure
        add_record_v3(params, record, folder_uid)  # Adjust call
    # Collect context from records (assume get all in root and subs)
    context = {'customer_name': customer['name']}
    records = get_folder_records(params, root_folder_uid)
    for title, data in records.items():
        for field, value in data.items():
            context[f'{title}_{field}'] = value
    word_stream = download_word_template(params, word_uid)
    doc = DocxTemplate(word_stream)
    doc.render(context)
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
        doc.save(tmp_docx.name)
        tmp_docx_path = tmp_docx.name
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
        tmp_pdf_path = tmp_pdf.name
    word_app = win32com.client.Dispatch('Word.Application')
    word_doc = word_app.Documents.Open(tmp_docx_path)
    word_doc.SaveAs(tmp_pdf_path, FileFormat=17)  # 17 = PDF
    word_doc.Close()
    word_app.Quit()
    with open(tmp_pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    os.remove(tmp_docx_path)
    os.remove(tmp_pdf_path)
    # Create PDF record
    pdf_record = RecordV3()
    pdf_record.title = f"{customer['name']}_Credentials.pdf"
    pdf_record.set_field('fileRef', {'name': pdf_record.title, 'size': len(pdf_bytes)})  # v3 file structure
    add_record_v3(params, pdf_record, root_folder_uid)
    # Upload attachment
    upload_task = UploadTask()
    upload_task.name = pdf_record.title
    upload_task.content = pdf_bytes
    upload_attachments(params, pdf_record, [upload_task])
    # TODO: Sharing and ACLs
    created_uids = [root_folder_uid] + [sub_uid for sub_uid in subfolder_uids.values()] + [pdf_record.record_uid]
    try:
        # Real ACL: Assume root is shared, set permissions
        rq = enterprise_pb2.SetSharedFolderPermissionRequest()  # Adjust based on proto
        rq.sharedFolderUid = utils.base64_url_decode(root_folder_uid)
        rq.manageUsers = False  # Example
        api.communicate_rest(params, rq, 'enterprise/set_shared_folder_permission')
        # Expand sharing
        share_cmd = OneTimeShareCreateCommand()
        link = share_cmd.execute(params, record=pdf_record.record_uid, name='PDF Share', expire_in_days=7)  # Adjust params
        logging.info(f'One-Time Share Link for {customer["name"]}: {link}')
    except Exception as e:
        logging.error(f'Error processing {customer["name"]}: {e}')
        # Rollback: delete created
        for uid in created_uids:
            if 'folder' in uid:  # Check type
                delete_folder(params, uid)
            else:
                api.delete_record(params, uid)  # Or folder delete
        raise

def main():
    parser = argparse.ArgumentParser(description='Keeper Credential PDF Generator')
    parser.add_argument('--bulk', action='store_true', help='Enable bulk mode')
    parser.add_argument('--csv', type=str, help='Path to CSV file for bulk input')
    parser.add_argument('--customer', action='append', help='Customer data in format "name:email:custom_param" (repeatable)')
    parser.add_argument('--lang', choices=['en', 'de'], default='en', help='Language for prompts (en/de)')
    args = parser.parse_args()

    # Initialize Keeper params
    keeper_params = params.KeeperParams()
    authenticate(keeper_params)

    # Interactive prompts for templates and folders
    json_uid = get_user_input('json_uid', lambda x: validate_record_uid(x, keeper_params), args.lang)
    word_uid = get_user_input('word_uid', lambda x: validate_record_uid(x, keeper_params), args.lang)
    source_folder = get_user_input('source_folder', lambda x: validate_folder(x, keeper_params), args.lang)
    target_folder = get_user_input('target_folder', lambda x: validate_folder(x, keeper_params), args.lang)

    # Collect customer data
    customers = []
    if args.bulk:
        if args.csv:
            with open(args.csv, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:  # Assume columns: name, email, custom_param
                        customers.append({'name': row[0], 'email': row[1] if len(row) > 1 else '', 'custom': row[2] if len(row) > 2 else ''})
        elif args.customer:
            for cust in args.customer:
                parts = cust.split(':')
                customers.append({'name': parts[0], 'email': parts[1] if len(parts) > 1 else '', 'custom': parts[2] if len(parts) > 2 else ''})
    else:
        # Single customer prompt
        name = get_user_input('name', lang=args.lang)
        email = get_user_input('email', lang=args.lang)
        custom = get_user_input('custom', lang=args.lang)
        customers.append({'name': name, 'email': email, 'custom': custom})

    # Process each customer
    for cust in customers:
        json_template = download_json_template(keeper_params, json_uid)
        # word_stream = download_word_template(keeper_params, word_uid)  # For later PDF step
        process_customer(keeper_params, cust, json_template, target_folder)  # Pass resolved target UID
    logging.info('Process completed.')

if __name__ == '__main__':
    main() 