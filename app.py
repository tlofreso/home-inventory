from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = ''  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///home_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
            db.session.commit()
            flash('Item added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
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
            db.session.commit()
            flash('Item updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error updating item: {str(e)}', 'error')
            db.session.rollback()

    return render_template('edit.html', item=item)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'error')
        db.session.rollback()
    return redirect(url_for('index'))

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

# Initialize the database
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()  # Initialize database before running
    app.run(debug=True)