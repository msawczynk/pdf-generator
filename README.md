# Keeper Credential PDF Generator

## Overview
This Python script automates generating customer-specific credentials in Keeper Vault, filling a Word template, creating PDFs, and sharing via one-time links. All data stays in the vault for security.

## Features
- Interactive prompts for inputs
- Bulk processing via CSV or CLI
- Credential autogeneration
- PDF creation from Word template
- One-time share links
- German language support (--lang de)

## Setup
1. Clone Keeper Commander: Already in workspace.
2. Install deps: `pip install -r requirements.txt`
3. Prepare Keeper: Records with JSON (notes) and Word attachment.

## Usage
```bash
python keeper_pdf_generator.py [--bulk] [--csv file.csv] [--customer "name:email:custom"] [--lang de]
```
- Interactive: Follow prompts.
- Bulk: Use --csv or repeat --customer.

## JSON Template Example
Store in record notes:
```json
{ "root_folder": "${customer_name}_Credentials", ... }
```

## Notes
- Runs on Windows for Word conversion.
- Customize for your vault. 