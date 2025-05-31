from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///home_inventory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

db = SQLAlchemy(app)

class Item(db.Model):
    __tablename__ = 'items'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100))
    model_number = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    manufactured_date = db.Column(db.Date)
    description = db.Column(db.Text)
    friendly_name = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to attachments
    attachments = db.relationship('Attachment', backref='item', lazy=True, cascade='all, delete-orphan')

class Attachment(db.Model):
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_number': self.model_number,
            'serial_number': self.serial_number,
            'manufacturer': self.manufacturer,
            'manufactured_date': self.manufactured_date.strftime('%Y-%m-%d') if self.manufactured_date else None,
            'description': self.description,
            'friendly_name': self.friendly_name,
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else None,
            'purchase_price': self.purchase_price,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

def validate_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def validate_price(price_str):
    if not price_str:
        return None
    try:
        return float(price_str)
    except ValueError:
        return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_attachment(file, item_id):
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        # Create unique filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + original_filename
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create attachment record
        attachment = Attachment(
            item_id=item_id,
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            content_type=file.content_type
        )
        
        db.session.add(attachment)
        return attachment
    return None

@app.route('/')
def index():
    items = Item.query.order_by(Item.created_at.desc()).all()
    return render_template('index.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        # Get form data
        manufactured_date = validate_date(request.form.get('manufactured_date'))
        purchase_date = validate_date(request.form.get('purchase_date'))
        purchase_price = validate_price(request.form.get('purchase_price'))

        # Create new item
        item = Item(
            model_name=request.form.get('model_name'),
            model_number=request.form.get('model_number'),
            serial_number=request.form.get('serial_number'),
            manufacturer=request.form.get('manufacturer'),
            manufactured_date=manufactured_date,
            description=request.form.get('description'),
            friendly_name=request.form.get('friendly_name'),
            purchase_date=purchase_date,
            purchase_price=purchase_price
        )

        try:
            db.session.add(item)
            db.session.flush()  # Get the item ID before committing
            
            # Handle file uploads
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename:
                    save_attachment(file, item.id)
            
            db.session.commit()
            flash('Item added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    item = Item.query.get_or_404(id)
    
    if request.method == 'POST':
        item.model_name = request.form.get('model_name')
        item.model_number = request.form.get('model_number')
        item.serial_number = request.form.get('serial_number')
        item.manufacturer = request.form.get('manufacturer')
        item.manufactured_date = validate_date(request.form.get('manufactured_date'))
        item.description = request.form.get('description')
        item.friendly_name = request.form.get('friendly_name')
        item.purchase_date = validate_date(request.form.get('purchase_date'))
        item.purchase_price = validate_price(request.form.get('purchase_price'))

        try:
            # Handle file uploads
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename:
                    save_attachment(file, item.id)
            
            db.session.commit()
            flash('Item updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error updating item: {str(e)}', 'danger')
            db.session.rollback()

    return render_template('edit.html', item=item)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    try:
        # Delete associated files from filesystem
        for attachment in item.attachments:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'danger')
        db.session.rollback()
    return redirect(url_for('index'))

@app.route('/attachment/<int:attachment_id>')
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], attachment.filename, 
                             as_attachment=True, download_name=attachment.original_filename)

@app.route('/delete_attachment/<int:attachment_id>', methods=['POST'])
def delete_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    item_id = attachment.item_id
    
    try:
        # Delete file from filesystem
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(attachment)
        db.session.commit()
        flash('Attachment deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting attachment: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('edit_item', id=item_id))

@app.route('/delete_attachments_bulk', methods=['POST'])
def delete_attachments_bulk():
    attachment_ids = request.form.getlist('attachment_ids')
    
    if not attachment_ids:
        flash('No attachments selected for deletion.', 'warning')
        return redirect(request.referrer or url_for('index'))
    
    item_id = None
    deleted_count = 0
    
    try:
        for attachment_id in attachment_ids:
            attachment = Attachment.query.get(attachment_id)
            if attachment:
                if item_id is None:
                    item_id = attachment.item_id
                
                # Delete file from filesystem
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                db.session.delete(attachment)
                deleted_count += 1
        
        db.session.commit()
        
        if deleted_count > 0:
            flash(f'Successfully deleted {deleted_count} attachment(s).', 'success')
        else:
            flash('No attachments were deleted.', 'warning')
            
    except Exception as e:
        flash(f'Error deleting attachments: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('edit_item', id=item_id) if item_id else url_for('index'))

@app.template_filter('format_date')
def format_date(date):
    if date:
        return date.strftime('%Y-%m-%d')
    return ''

@app.template_filter('format_price')
def format_price(price):
    if price is not None:
        return f"${price:,.2f}"
    return ''

@app.template_filter('format_file_size')
def format_file_size(size_bytes):
    if size_bytes is None:
        return ''
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# Initialize the database
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()  # Initialize database before running
    app.run(debug=True)