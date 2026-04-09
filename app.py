# ...existing code...
import os

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash 
# Install the required packages
# pip install flask_sqlalchemy
# pip install flask-login
# ...existing code...

app = Flask(__name__)
# ...existing code...
# Use environment variables for secrets and DB URL
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-that-you-should-change')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://hotel_admin:postgres@localhost/hotel_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# ✅ ADD THIS BLOCK
with app.app_context():
    db.create_all()

    from setup_db import populate_database
    try:
        populate_database()
    except Exception as e:
        print("DB already populated or error:", e)
# ...existing code...


# --- Flask-Login Configuration ---
login_manager = LoginManager()
login_manager.init_app(app)
# If a user tries to access a protected page, redirect them to the 'login' page.
login_manager.login_view = 'login' 


# --- Database Models ---

# The UserMixin is required by Flask-Login. It adds default user methods.
class User(db.Model, UserMixin):
    __tablename__ = 'users' # Renamed to 'users' for clarity
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False) # Store hashed passwords
    orders = db.relationship('Order', backref='user', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100))
    hotel = db.Column(db.String(100), nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    items = db.Column(db.Text, nullable=False)
    total = db.Column(db.Float, nullable=False)
    # Link orders to a specific user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# --- User Loader for Flask-Login ---
# This function is required by Flask-Login to load the current user from the session.
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --- Application Routes ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''

        # Basic validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('signup'))
        if len(username) < 3 or len(password) < 6:
            flash('Username must be >=3 chars and password >=6 chars.', 'error')
            return redirect(url_for('signup'))
        if '@' not in email:
            flash('Invalid email address.', 'error')
            return redirect(url_for('signup'))

        # Check existence
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email address already registered. Please use a different one.', 'error')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Failed to create account. Try again.', 'error')
            return redirect(url_for('signup'))

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('login'))

        # If correct, log the user in
        login_user(user)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
@login_required # Only logged-in users can log out
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/')
def home():
    hotels_query = db.session.query(MenuItem.hotel).distinct().all()
    hotel_names = sorted([h[0] for h in hotels_query])
    return render_template('index.html', hotel_names=hotel_names)

# ...existing code...
@app.route('/hotel/<hotel_name>')
def hotel_page(hotel_name):
    # use pattern match so "Lazar" matches "Lazar Hotel" etc, or change to equality if exact match required
    items = MenuItem.query.filter(MenuItem.hotel.ilike(f'%{hotel_name}%')).order_by(MenuItem.id).all()
    if not items:
        flash(f"Sorry, the hotel '{hotel_name}' was not found.", "error")
        return redirect(url_for('home'))
    return render_template('hotel_menu.html', items=items, hotel_name=hotel_name)
# ...existing code...

@app.route('/address_form', methods=['GET', 'POST'])
@login_required
def address_form():
    if request.method == 'POST':
        name = request.form.get('fname')
        mobile = request.form.get('mobile')
        address = request.form.get('address')
        items_str = request.form.get('items')
        total_str = request.form.get('total')

        if not all([name, mobile, address, items_str, total_str]):
            flash('Please fill all fields to submit your order.', 'error')
            return redirect(url_for('home'))

        try:
            total_val = float(total_str)
        except (TypeError, ValueError):
            flash('Invalid total amount.', 'error')
            return redirect(url_for('home'))

        new_order = Order(
            name=name, mobile=mobile, address=address, items=items_str,
            total=total_val,
            user_id=current_user.id
        )
        try:
            db.session.add(new_order)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Failed to save order. Try again.', 'error')
            return redirect(url_for('home'))

        return render_template('order_confirmation.html',
                               name=name, phone=mobile, address=address,
                               items=items_str, total=f"{total_val:.2f}")

    # GET: render the address form (allow prefilled total/items via query params)
    total = request.args.get('total', '0.00')
    items = request.args.getlist('items')  # supports multiple ?items=...
    # pass items as a list or join into a string if your template expects that
    return render_template('address_form.html', total=total, items=items)

# ...existing code...

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')


if __name__ == '__main__':
    app.run()