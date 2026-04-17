from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE (RENDER POSTGRESQL) =================

DATABASE_URL = "postgresql://hotel_db54_user:6PGCftbCrnCYYBSDiJSI9gycs96u5fyV@dpg-d7gpk5reo5us739ie3og-a.oregon-postgres.render.com/hotel_db54"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,   # ✅ reconnect if connection is dead
    "pool_recycle": 280      # ✅ refresh connection before timeout
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    mobile = db.Column(db.String(20))
    street = db.Column(db.String(200))
    village = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))


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


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    item_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer, default=1)


# ✅ ORDER TABLES
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    address = db.Column(db.String(300))
    total = db.Column(db.Integer)
    status = db.Column(db.String(50), default="Preparing")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    item_name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)


# ================= HOME =================

@app.route('/')
def home():
    hotels = Hotel.query.all()
    return render_template('index.html', hotels=hotels)


@app.route('/hotel/<int:id>')
def hotel_menu(id):
    hotel = db.session.get(Hotel, id)
    items = MenuItem.query.filter_by(hotel_id=id).all()
    return render_template('menu.html', hotel=hotel, items=items)


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
        user = User.query.filter_by(
            email=request.form['email'],
            password=request.form['password']
        ).first()

        if user:
            session['user_id'] = user.id
            return redirect('/')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= CART =================

@app.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    if 'user_id' not in session:
        return redirect('/login')

    cart_item = Cart.query.filter_by(
        user_id=session['user_id'],
        item_id=item_id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        db.session.add(Cart(
            user_id=session['user_id'],
            item_id=item_id,
            quantity=1
        ))

    db.session.commit()
    return redirect(request.referrer or '/')


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    cart_items = Cart.query.filter_by(user_id=session['user_id']).all()

    items = []
    total = 0

    for c in cart_items:
        item = db.session.get(MenuItem, c.item_id)
        subtotal = item.price * c.quantity

        items.append({
            "id": item.id,
            "name": item.name,
            "price": item.price,
            "qty": c.quantity,
            "total": subtotal
        })

        total += subtotal

    return render_template('cart.html', items=items, total=total)


@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    Cart.query.filter_by(
        user_id=session['user_id'],
        item_id=item_id
    ).delete()
    db.session.commit()
    return redirect('/cart')


@app.route('/clear_cart')
def clear_cart():
    Cart.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()
    return redirect('/cart')


# ================= PLACE ORDER =================

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect('/login')

    cart_items = Cart.query.filter_by(user_id=session['user_id']).all()

    total = 0
    for c in cart_items:
        item = db.session.get(MenuItem, c.item_id)
        total += item.price * c.quantity

    address = f"{request.form['street']}, {request.form['city']}"

    order = Order(
        user_id=session['user_id'],
        address=address,
        total=total
    )
    db.session.add(order)
    db.session.commit()

    for c in cart_items:
        item = db.session.get(MenuItem, c.item_id)

        db.session.add(OrderItem(
            order_id=order.id,
            item_name=item.name,
            price=item.price,
            quantity=c.quantity
        ))

    Cart.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()

    return redirect(f'/order_success/{order.id}')


# ================= ORDERS =================

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect('/login')

    orders = Order.query.filter_by(user_id=session['user_id']).all()

    data = []
    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()
        data.append({"order": o, "items": items})

    return render_template('orders.html', order_data=data)


@app.context_processor
def inject_cart_count():
    if 'user_id' in session:
        count = db.session.query(db.func.sum(Cart.quantity))\
            .filter_by(user_id=session['user_id']).scalar()
        return dict(cart_count=count or 0)
    return dict(cart_count=0)


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    user = db.session.get(User, session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')

    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        user.name = request.form['name']
        user.mobile = request.form['mobile']
        user.street = request.form['street']
        user.village = request.form['village']
        user.city = request.form['city']
        user.state = request.form['state']
        user.pincode = request.form['pincode']

        db.session.commit()
        return redirect('/profile')

    return render_template('edit_profile.html', user=user)


@app.route('/contact')
def contact():
    return render_template('contact.html')


# ================= SEARCH =================

@app.route('/search')
def search():
    query = request.args.get('q')

    items = MenuItem.query.filter(
        MenuItem.name.ilike(f"%{query}%")
    ).all()

    return render_template('search.html', items=items, query=query)


# ================= ORDER TRACKING =================

@app.route('/track/<int:order_id>')
def track(order_id):
    order = db.session.get(Order, order_id)

    if not order:
        return "Order not found", 404

    return render_template('track.html', order=order)




@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    order = db.session.get(Order, order_id)

    items = OrderItem.query.filter_by(order_id=order_id).all()

    return render_template('order_success.html', order=order, items=items)


# ================= INIT =================

with app.app_context():
    db.create_all()

# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)