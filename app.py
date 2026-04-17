from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "secret123"

db_url = os.getenv("DATABASE_URL")

if db_url:
    db_url = db_url.replace("postgres://", "postgresql://")

    # ✅ THIS IS THE IMPORTANT LINE
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
else:
    db_url = "sqlite:///database.db"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    street = db.Column(db.String(100))
    village = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    mobile = db.Column(db.String(15))


class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    image = db.Column(db.String(100))


class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    image = db.Column(db.String(100))
    hotel_id = db.Column(db.Integer)
    rating = db.Column(db.Float, default=4.5)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    total = db.Column(db.Integer)
    address = db.Column(db.String(200))
    payment = db.Column(db.String(50), default="Cash on Delivery")
    status = db.Column(db.String(50), default="Preparing")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    item_name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)

# ================= INIT DB (IMPORTANT FOR RENDER) =================

with app.app_context():
    db.create_all()

    try:
        if Hotel.query.count() == 0:
            h1 = Hotel(name="Bhaskar Hotel", image="hotel2.jpg")
            h2 = Hotel(name="Lazar Hotel", image="hotel1.jpg")

            db.session.add_all([h1, h2])
            db.session.commit()

            items = [
                MenuItem(name="Chicken Biryani", price=150, image="chicken.jpg", hotel_id=h1.id),
                MenuItem(name="Chicken Fry", price=120, image="chicken_fry.jpg", hotel_id=h1.id),
                MenuItem(name="Veg Meals", price=80, image="meals.jpg", hotel_id=h1.id),

                MenuItem(name="Mutton Biryani", price=250, image="mutton.jpg", hotel_id=h2.id),
                MenuItem(name="Fish Fry", price=170, image="fish.jpg", hotel_id=h2.id),
                MenuItem(name="Fried Rice", price=130, image="fried_rice.jpg", hotel_id=h2.id),
            ]

            db.session.add_all(items)
            db.session.commit()

    except Exception as e:
        print("DB INIT ERROR:", e)
# ================= ROUTES =================

@app.route('/')
def home():
    hotels = Hotel.query.all()
    return render_template('index.html', hotels=hotels)


@app.route('/hotel/<int:id>')
def hotel_menu(id):
    hotel = Hotel.query.get(id)
    items = MenuItem.query.filter_by(hotel_id=id).all()
    return render_template('menu.html', hotel=hotel, items=items)


# ================= CART =================

@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    cart = session.get('cart', {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session['cart'] = cart
    session['cart_count'] = sum(cart.values())
    return redirect(request.referrer or '/')


@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0

    for item_id, qty in cart.items():
        item = MenuItem.query.get(int(item_id))
        if item:
            subtotal = item.price * qty
            total += subtotal
            items.append({'name': item.name, 'qty': qty, 'total': subtotal})

    return render_template('cart.html', items=items, total=total)


# ================= AUTH =================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=request.form['password'],
            mobile=request.form['mobile']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.password == request.form['password']:
            session['user'] = user.name
            session['user_id'] = user.id
            return redirect('/')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= ORDER =================

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect('/login')

    cart = session.get('cart')
    if not cart:
        return "Cart is empty ❌"

    street = request.form.get('street')
    village = request.form.get('village')
    city = request.form.get('city')
    state = request.form.get('state')
    pincode = request.form.get('pincode')

    full_address = f"{street}, {village}, {city}, {state} - {pincode}"

    order = Order(
        user_id=session['user_id'],
        address=full_address,
        status="Placed",
        total=0
    )

    db.session.add(order)
    db.session.commit()

    total_price = 0

    for item_id, qty in cart.items():
        item = MenuItem.query.get(int(item_id))
        if item:
            total_price += item.price * qty

            order_item = OrderItem(
                order_id=order.id,
                item_name=item.name,
                price=item.price,
                quantity=qty
            )
            db.session.add(order_item)

    order.total = total_price
    db.session.commit()

    session['cart'] = {}
    session['cart_count'] = 0

    return redirect(f"/order_success/{order.id}")


@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect('/login')

    orders = Order.query.filter_by(user_id=session['user_id']).all()
    order_data = []

    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()
        order_data.append({"order": o, "items": items})

    return render_template('orders.html', order_data=order_data)


@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    order = Order.query.get(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template('order_success.html', order=order, items=items)


# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)