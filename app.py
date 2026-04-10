import os
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# APP CONFIG
# =========================

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///local.db'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ✅ IMPORTANT: CREATE TABLES (WORKS ON RENDER)
with app.app_context():
    db.create_all()

# =========================
# LOGIN SETUP
# =========================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =========================
# MODELS
# =========================

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # PROFILE FIELDS
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(20))
    address = db.Column(db.String(300))

    orders = db.relationship('Order', backref='user', lazy=True)


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    image = db.Column(db.String(100))
    hotel = db.Column(db.String(100))


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    mobile = db.Column(db.String(15))
    address = db.Column(db.String(200))
    items = db.Column(db.Text)
    total = db.Column(db.Float)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# =========================
# USER LOADER
# =========================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    hotels = db.session.query(MenuItem.hotel).distinct().all()
    hotel_names = sorted([h[0] for h in hotels])
    return render_template('index.html', hotel_names=hotel_names)


@app.route('/hotel/<hotel_name>')
def hotel_page(hotel_name):
    items = MenuItem.query.filter(MenuItem.hotel.ilike(f'%{hotel_name}%')).all()
    return render_template('hotel_menu.html', items=items, hotel_name=hotel_name)


# =========================
# AUTH
# =========================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))

        hashed = generate_password_hash(password)
        user = User(username=username, email=email, password_hash=hashed)

        db.session.add(user)
        db.session.commit()

        flash('Signup successful!', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()

        if not user or not check_password_hash(user.password_hash, request.form.get('password')):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# =========================
# ADDRESS + ORDER
# =========================

@app.route('/address_form', methods=['GET', 'POST'])
@login_required
def address_form():
    if request.method == 'POST':
        name = request.form.get('fname')
        mobile = request.form.get('mobile')
        address = request.form.get('address')
        items = request.form.get('items')
        total = float(request.form.get('total'))

        # SAVE PROFILE
        current_user.name = name
        current_user.mobile = mobile
        current_user.address = address
        db.session.commit()

        # SAVE ORDER
        order = Order(
            name=name,
            mobile=mobile,
            address=address,
            items=items,
            total=total,
            user_id=current_user.id
        )

        db.session.add(order)
        db.session.commit()

        return render_template('order_confirmation.html',
                               name=name,
                               phone=mobile,
                               address=address,
                               items=items,
                               total=total)

    total = request.args.get('total', '0')
    items = request.args.getlist('items')

    return render_template('address_form.html', total=total, items=items)


# =========================
# PROFILE
# =========================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.mobile = request.form.get('mobile')
        current_user.address = request.form.get('address')

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')


# =========================
# ORDER HISTORY
# =========================

@app.route('/orders')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id)\
                        .order_by(Order.id.desc()).all()

    return render_template('orders.html', orders=orders)


@app.route('/contact_us')
def contact():
    return render_template('contact_us.html')


# =========================
# RUN
# =========================

if __name__ == '__main__':
    app.run(debug=True)