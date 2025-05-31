# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a Flask-based home inventory management application that allows users to track household items with detailed information including serial numbers, model numbers, purchase dates, and file attachments. The application was created to solve the problem of quickly accessing item details during recalls (like retrieving car seat serial numbers) and storing related documents like receipts and manuals.

## Running the Application

### Environment Setup
1. Copy `.env.example` to `.env` and configure as needed:
```bash
cp .env.example .env
```

2. Set required environment variables (or use defaults):
```bash
export SECRET_KEY="your-secure-secret-key"
export DATABASE_URL="sqlite:///home_inventory.db"  # Optional, defaults to SQLite
```

### Starting the Application
```bash
source ./.venv/bin/activate  # Activate virtual environment
python app.py
```

The application will:
- Initialize the SQLite database (`home_inventory.db`) 
- Create the `uploads/` directory for file storage
- Start the Flask development server on debug mode
- Create database tables automatically on first run

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | No | `dev-secret-key-change-in-production` | Flask secret key for sessions and CSRF protection |
| `DATABASE_URL` | No | `sqlite:///home_inventory.db` | Database connection string |
| `FLASK_ENV` | No | Not set | Flask environment (development/production) |
| `FLASK_DEBUG` | No | Not set | Enable Flask debug mode (true/false) |

### Generating a Secure Secret Key
For production, generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Architecture

- **Backend**: Flask application (`app.py`) with SQLAlchemy ORM
- **Database**: SQLite (`home_inventory.db`) with `items` and `attachments` tables
- **File Storage**: Local filesystem (`uploads/` directory) with 16MB file size limit
- **Frontend**: Jinja2 templates in `templates/` directory using Bootstrap 5 and Bootstrap Icons
- **Data Model**: `Item` and `Attachment` models with one-to-many relationship

## Key Components

- `Item` model (`app.py:12-26`): SQLAlchemy model representing inventory items
- `Attachment` model (`app.py:28-36`): SQLAlchemy model for file attachments linked to items
- Route handlers (`app.py:112-269`): CRUD operations for items and attachments
- File handling (`app.py:79-110`): Upload, validation, and deletion utilities
- Template filters (`app.py:271-283`): Custom filters for date, price, and file size formatting
- Base template (`templates/base.html`): Bootstrap-based layout with navigation, DataTables, and Bootstrap Icons

## Database Schema

### Items Table
- Identification: model_name, model_number, serial_number, manufacturer
- Dates: manufactured_date, purchase_date, created_at
- Financial: purchase_price
- Metadata: description, friendly_name

### Attachments Table
- item_id: Foreign key to items table
- filename: Unique system filename (timestamped)
- original_filename: User's original filename
- file_size: Size in bytes
- content_type: MIME type
- created_at: Upload timestamp

## File Management

### Supported File Types
- Documents: `.txt`, `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`
- Images: `.png`, `.jpg`, `.jpeg`, `.gif`

### File Operations
- **Upload**: Multiple files during item creation/editing
- **Download**: Click attachment name to download with original filename
- **Delete**: Individual deletion via trash icon or bulk deletion with checkboxes
- **Storage**: Files stored in `uploads/` with timestamped filenames to prevent conflicts

## Form Validation

- `validate_date()`: Parses YYYY-MM-DD format dates
- `validate_price()`: Converts strings to float values
- `allowed_file()`: Validates file extensions against whitelist
- `save_attachment()`: Handles file upload, naming, and database record creation