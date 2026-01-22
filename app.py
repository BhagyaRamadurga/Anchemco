import os
import re
import pytz
from flask import Flask, render_template, redirect, url_for, flash, request, send_file, send_from_directory


from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime

# Initialize App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_for_dev')
app.config['UPLOAD_FOLDER'] = 'uploads'


# Database Config
# Use Postgres if available (Render), else SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///sharanu_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    entries = db.relationship('ProductionEntry', backref='user', lazy=True)

class ProductionEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(150))
    authorised_person = db.Column(db.String(150))
    employee_id = db.Column(db.String(50))
    final_batch_number = db.Column(db.String(50))
    final_batch_number = db.Column(db.String(50))
    sf_batch_number = db.Column(db.String(50))
    batch_quantity = db.Column(db.String(50))
    urea_percentage = db.Column(db.Float)
    density = db.Column(db.Float)
    photo_path = db.Column(db.String(300))
    density = db.Column(db.Float)
    photo_path = db.Column(db.String(300))
    # Use function to get current IST time
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('landing'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('landing'))
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        # flash('Please check your login details and try again.', 'danger') # Removed flash
        return render_template('auth.html', login_error='Please check your login details and try again.', active_tab='login')
    
    login_user(user)
    login_user(user)
    return redirect(url_for('landing'))

@app.route('/home')
@login_required
def landing():
    return render_template('home.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    # Password Complexity Validation
    if len(password) < 6:
        return render_template('auth.html', signup_error='Password must be at least 6 characters long.', active_tab='signup')
    if not re.search(r"[A-Z]", password):
        return render_template('auth.html', signup_error='Password must contain at least one uppercase letter.', active_tab='signup')
    if not re.search(r"[0-9]", password):
        return render_template('auth.html', signup_error='Password must contain at least one number.', active_tab='signup')
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return render_template('auth.html', signup_error='Password must contain at least one special character.', active_tab='signup')

    if password != confirm_password:
        return render_template('auth.html', signup_error='Passwords do not match!', active_tab='signup')
    
    user_by_name = User.query.filter_by(username=username).first()
    if user_by_name:
        return render_template('auth.html', signup_error='Username already exists.', active_tab='signup')
        
    user_by_email = User.query.filter_by(email=email).first()
    if user_by_email:
        return render_template('auth.html', signup_error='Email already registered.', active_tab='signup')
    
    new_user = User(username=username, email=email, password_hash=generate_password_hash(password, method='scrypt'))
    db.session.add(new_user)
    db.session.commit()
    
    # login_user(new_user) # Logic Changed: Redirect to login
    return render_template('auth.html', login_message='Signup successful! Please login.', active_tab='login')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/dashboard')
@login_required
def dashboard():
    # Show ALL entries, not just current user's
    entries = ProductionEntry.query.order_by(ProductionEntry.timestamp.desc()).all()
    return render_template('dashboard.html', entries=entries)

@app.route('/entry')
@login_required
def new_entry():
    return render_template('form.html')

@app.route('/save_entry', methods=['POST'])
@login_required
def save_entry():
    try:
        photo = request.files['photo']
        filename = None
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            # Add timestamp to filename to prevent duplicates
            timestamp_str = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp_str}_{filename}"
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


        new_entry = ProductionEntry(
            user_id=current_user.id,
            company_name="Sharanu",
            authorised_person=request.form.get('authorised_person'),
            employee_id=request.form.get('employee_id'),
            final_batch_number=request.form.get('final_batch_number'),
            sf_batch_number="SF AdBlue",
            batch_quantity=request.form.get('batch_quantity'),
            urea_percentage=float(request.form.get('urea_percentage')),
            density=float(request.form.get('density')),
            photo_path=filename
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('Entry saved successfully!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error saving entry: {str(e)}', 'danger')
        return redirect(url_for('new_entry'))

@app.route('/delete_entry/<int:entry_id>')
@login_required
def delete_entry(entry_id):
    entry = ProductionEntry.query.get(entry_id)
    if entry:
        # Optional: Check if user owns entry? User wanted global dashboard, so global delete?
        # Assuming global delete is fine since dashboard is global.
        # But for safety, maybe restrict? 
        # The prompt says "user can detele the entries", implies ANY user can delete ANY entry if they can see it.
        db.session.delete(entry)
        db.session.commit()
        flash('Entry deleted successfully.', 'success')
    else:
        flash('Entry not found.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/download_excel')
@login_required
def download_excel():
    # Download ALL entries
    entries = ProductionEntry.query.all()
    
    data = []
    for e in entries:
        data.append({
            'ID': e.id,
            'Date': e.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Company': e.company_name,
            'Auth Person': e.authorised_person,
            'Employee ID': e.employee_id,
            'Product': e.sf_batch_number,
            'Final Batch': e.final_batch_number,
            'Batch Quantity': e.batch_quantity,
            'Urea %': e.urea_percentage,
            'Density': e.density,
            'Photo': e.photo_path
        })
    
    
    df = pd.DataFrame(data)
    current_time_str = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y%m%d')
    filename = f"production_data_global_{current_time_str}.xlsx"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    df.to_excel(filepath, index=False)
    
    return send_file(filepath, as_attachment=True)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(app.static_folder, 'service-worker.js')



@app.route('/fix_db')
def fix_db():
    try:
        # Attempt to add the column. Works for SQLite and Postgres (mostly)
        # For Postgres specifically:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE production_entry ADD COLUMN IF NOT EXISTS batch_quantity VARCHAR(50)"))
            conn.commit()
        return "Database fixed! Column 'batch_quantity' added."
    except Exception as e:
        return f"Error or already exists: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
