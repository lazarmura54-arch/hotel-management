import os
from app import app, db, MenuItem

with app.app_context():

    db.create_all()

    if MenuItem.query.count() == 0:
        items = [
            MenuItem(name='Chicken Curry', price=150.0, image='chicken.jpeg', hotel='Lazar Hotel'),
            MenuItem(name='Egg Curry', price=120.0, image='egg.jpeg', hotel='Lazar Hotel'),
            MenuItem(name='Mutton Fry', price=200.0, image='mutton3.jpeg', hotel='Lazar Hotel'),
            MenuItem(name='Veg Meals', price=90.0, image='meals1.jpeg', hotel='Lazar Hotel'),
            MenuItem(name='Curd Rice', price=50.0, image='curd rice.jpeg', hotel='Lazar Hotel'),
            MenuItem(name='Fish Biryani', price=150.0, image='fish1.jpeg', hotel='Lazar Hotel'),

            MenuItem(name='Chicken Curry', price=160.0, image='chicken.jpeg', hotel='Nani Hotel'),
            MenuItem(name='Veg Meals', price=100.0, image='meals1.jpeg', hotel='Nani Hotel'),
        ]

        db.session.add_all(items)
        db.session.commit()

        print("✅ Menu items inserted!")
    else:
        print("⚠️ Data already exists")