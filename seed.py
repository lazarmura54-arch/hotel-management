from app import app, db, Hotel, MenuItem

with app.app_context():
    # Clear old data (optional)
    db.session.query(MenuItem).delete()
    db.session.query(Hotel).delete()
    db.session.commit()

    # Add 4 hotels
    h1 = Hotel(name="Bhaskar Hotel", image="hotel2.jpg")
    h2 = Hotel(name="Lazar Hotel", image="hotel1.jpg")
    h3 = Hotel(name="Mariyamma Hotel", image="mariyamma.jpg")
    h4 = Hotel(name="Nani Hotel", image="nani.jpg")

    db.session.add_all([h1, h2, h3, h4])
    db.session.commit()

    # Add 9 items per hotel
    items = [
        # Hotel 1
        MenuItem(name="Chicken Biryani", price=150, image="chicken.jpg", hotel_id=h1.id),
        MenuItem(name="Chicken Fry", price=120, image="chicken_fry.jpg", hotel_id=h1.id),
        MenuItem(name="Meals", price=80, image="meals.jpg", hotel_id=h1.id),
        MenuItem(name="Curd Rice", price=70, image="curd.jpg", hotel_id=h1.id),
        MenuItem(name="Fried Rice", price=130, image="fried_rice.jpg", hotel_id=h1.id),
        MenuItem(name="Veg Rice", price=100, image="veg.jpg", hotel_id=h1.id),
        MenuItem(name="Fish Fry", price=160, image="fish2.jpg", hotel_id=h1.id),
        MenuItem(name="Gobi Rice", price=110, image="gobi_rice.jpg", hotel_id=h1.id),

        # Hotel 2
        MenuItem(name="Mutton Biryani", price=250, image="mutton1.jpg", hotel_id=h2.id),
        MenuItem(name="Fish Fry", price=170, image="fish2.jpg", hotel_id=h2.id),
        MenuItem(name="Meals", price=90, image="meals.jpg", hotel_id=h2.id),
        MenuItem(name="Curd Rice", price=80, image="curd.jpg", hotel_id=h2.id),
        MenuItem(name="Fried Rice", price=140, image="fried_rice.jpg", hotel_id=h2.id),
        MenuItem(name="Chicken Fry", price=130, image="chicken_fry.jpg", hotel_id=h2.id),
        MenuItem(name="Veg Rice", price=110, image="veg.jpg", hotel_id=h2.id),
        MenuItem(name="Gobi Rice", price=120, image="gobi_rice.jpg", hotel_id=h2.id),

        # Hotel 3
        MenuItem(name="Chicken Fry", price=140, image="chicken11.jpg", hotel_id=h3.id),
        MenuItem(name="Fish Fry", price=160, image="fish2.jpg", hotel_id=h3.id),
        MenuItem(name="Meals", price=85, image="meals2.jpg", hotel_id=h3.id),
        MenuItem(name="Curd Rice", price=75, image="curd1.jpg", hotel_id=h3.id),
        MenuItem(name="Fried Rice", price=135, image="fried_rice.jpg", hotel_id=h3.id),
        MenuItem(name="Veg Rice", price=105, image="veg.jpg", hotel_id=h3.id),
        MenuItem(name="Chicken Biryani", price=160, image="chicken3.jpg", hotel_id=h3.id),
        MenuItem(name="Gobi Rice", price=115, image="gobi_rice.jpg", hotel_id=h3.id),

        # Hotel 4
        MenuItem(name="Fish Fry", price=180, image="fish2.jpg", hotel_id=h4.id),
        MenuItem(name="Meals", price=85, image="meals3.jpg", hotel_id=h4.id),
        MenuItem(name="Chicken Fry", price=130, image="chicken_fry.jpg", hotel_id=h4.id),
        MenuItem(name="Curd Rice", price=70, image="curd1.jpg", hotel_id=h4.id),
        MenuItem(name="Fried Rice", price=140, image="fried_rice.jpg", hotel_id=h4.id),
        MenuItem(name="Veg Rice", price=110, image="veg.jpg", hotel_id=h4.id),
        MenuItem(name="Mutton Biryani", price=260, image="mutton1.jpg", hotel_id=h4.id),
        MenuItem(name="Gobi Rice", price=120, image="gobi_rice.jpg", hotel_id=h4.id),
    ]

    db.session.add_all(items)
    db.session.commit()

    print("✅ PostgreSQL Database Seeded Successfully!")