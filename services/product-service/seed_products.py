import requests
from urllib.parse import quote_plus
from app.database import SessionLocal, engine, Base
from app.models import Product, Category

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def get_or_create_category(name: str, description: str = ""):
    category = db.query(Category).filter(Category.name == name).first()
    if category:
        return category
    category = Category(name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

def seed_from_fake_store_api():
    print("Fetching products from Fake Store API...")
    response = requests.get("https://fakestoreapi.com/products")
    response.raise_for_status()
    products = response.json()

    for item in products:
        category_name = item["category"].title()  # e.g. "electronics" -> "Electronics"
        category = get_or_create_category(category_name, f"{category_name} products")

        existing = db.query(Product).filter(Product.name == item["title"]).first()
        if existing:
            continue  # avoid duplicate inserts if script is re-run

        product = Product(
            name=item["title"],
            description=item["description"],
            price=item["price"],
            stock_quantity=50,  # not provided by API, defaulting
            image_url=item["image"],
            category_id=category.id
        )
        db.add(product)

    db.commit()
    print(f"Seeded {len(products)} products from Fake Store API.")

def seed_manual_products():
    print("Adding manually curated products...")

    manual_products = [
        {
            "name": "Wireless Gaming Mouse",
            "description": "High-precision wireless gaming mouse with RGB lighting and programmable buttons",
            "price": 45.99,
            "stock_quantity": 30,
            "image_url": "https://placehold.co/300x300?text=Gaming+Mouse",
            "category": "Electronics"
        },
        {
            "name": "Mechanical Keyboard",
            "description": "Compact mechanical keyboard with blue switches, ideal for typing and gaming",
            "price": 79.99,
            "stock_quantity": 25,
            "image_url": "https://placehold.co/300x300?text=Keyboard",
            "category": "Electronics"
        },
        {
            "name": "Noise Cancelling Headphones",
            "description": "Over-ear wireless headphones with active noise cancellation and 30-hour battery life",
            "price": 129.99,
            "stock_quantity": 20,
            "image_url": "https://placehold.co/300x300?text=Headphones",
            "category": "Electronics"
        },
        {
            "name": "Portable Bluetooth Speaker",
            "description": "Compact waterproof speaker with deep bass and 12-hour playtime",
            "price": 34.99,
            "stock_quantity": 40,
            "image_url": "https://placehold.co/300x300?text=Speaker",
            "category": "Electronics"
        },
        {
            "name": "Smartwatch Fitness Tracker",
            "description": "Tracks heart rate, sleep, and steps with a 7-day battery life",
            "price": 59.99,
            "stock_quantity": 35,
            "image_url": "https://placehold.co/300x300?text=Smartwatch",
            "category": "Electronics"
        },
        {
            "name": "Men'S Cotton Hoodie",
            "description": "Soft cotton-blend hoodie, relaxed fit, available in multiple colors",
            "price": 29.99,
            "stock_quantity": 60,
            "image_url": "https://placehold.co/300x300?text=Hoodie",
            "category": "Men'S Clothing"
        },
        {
            "name": "Men'S Slim Fit Jeans",
            "description": "Stretchable slim-fit denim jeans, mid-rise, everyday wear",
            "price": 39.99,
            "stock_quantity": 45,
            "image_url": "https://placehold.co/300x300?text=Jeans",
            "category": "Men'S Clothing"
        },
        {
            "name": "Men'S Casual Sneakers",
            "description": "Lightweight breathable sneakers, ideal for daily casual wear",
            "price": 49.99,
            "stock_quantity": 30,
            "image_url": "https://placehold.co/300x300?text=Sneakers",
            "category": "Men'S Clothing"
        },
        {
            "name": "Women'S Floral Summer Dress",
            "description": "Lightweight floral print dress, perfect for casual summer outings",
            "price": 34.99,
            "stock_quantity": 40,
            "image_url": "https://placehold.co/300x300?text=Summer+Dress",
            "category": "Women'S Clothing"
        },
        {
            "name": "Women'S Denim Jacket",
            "description": "Classic denim jacket with button closure, versatile everyday layering piece",
            "price": 44.99,
            "stock_quantity": 25,
            "image_url": "https://placehold.co/300x300?text=Denim+Jacket",
            "category": "Women'S Clothing"
        },
        {
            "name": "Women'S Yoga Leggings",
            "description": "High-waisted stretch leggings designed for yoga and everyday activewear",
            "price": 24.99,
            "stock_quantity": 55,
            "image_url": "https://placehold.co/300x300?text=Leggings",
            "category": "Women'S Clothing"
        },
    ]

    for item in manual_products:
        existing = db.query(Product).filter(Product.name == item["name"]).first()
        if existing:
            continue

        category = get_or_create_category(item["category"])

        product = Product(
            name=item["name"],
            description=item["description"],
            price=item["price"],
            stock_quantity=item["stock_quantity"],
            image_url=item["image_url"],
            category_id=category.id
        )
        db.add(product)

    db.commit()
    print(f"Added {len(manual_products)} manually curated products.")


# (category, name, description, price, stock)
CATALOG = [
    # --- Electronics ---
    ("Electronics", "USB-C Fast Charger 65W", "Compact GaN wall charger that fast-charges laptops, tablets and phones through one USB-C port", 29.99, 80),
    ("Electronics", "4K Webcam with Microphone", "Ultra HD webcam with autofocus and built-in noise-reducing microphone for video calls and streaming", 69.99, 25),
    ("Electronics", "Wireless Earbuds Pro", "True wireless earbuds with active noise cancellation, touch controls and a 24-hour charging case", 89.99, 50),
    ("Electronics", "Portable Power Bank 20000mAh", "High-capacity power bank with dual USB output and fast charging for phones and tablets", 39.99, 60),
    ("Electronics", "27-inch IPS Monitor", "Full HD IPS monitor with thin bezels, 75Hz refresh rate and eye-care flicker-free backlight", 159.99, 15),
    ("Electronics", "Laptop Stand Aluminium", "Adjustable ergonomic aluminium laptop stand that improves airflow and desk posture", 27.99, 70),
    # --- Home & Kitchen ---
    ("Home & Kitchen", "Stainless Steel Water Bottle", "Double-wall insulated bottle that keeps drinks cold for 24 hours or hot for 12 hours", 19.99, 100),
    ("Home & Kitchen", "Non-Stick Frying Pan", "26 cm non-stick frying pan with a stay-cool handle, suitable for induction and gas stoves", 24.99, 45),
    ("Home & Kitchen", "Electric Kettle 1.8L", "Fast-boil stainless steel electric kettle with auto shut-off and boil-dry protection", 32.99, 40),
    ("Home & Kitchen", "Ceramic Coffee Mug Set", "Set of four 350 ml ceramic coffee mugs, dishwasher and microwave safe", 22.99, 55),
    ("Home & Kitchen", "Bamboo Cutting Board", "Large eco-friendly bamboo chopping board with juice groove and easy-grip handles", 17.99, 65),
    ("Home & Kitchen", "Memory Foam Pillow", "Contour memory foam pillow with breathable cover that supports the neck and shoulders", 26.99, 50),
    ("Home & Kitchen", "LED Desk Lamp", "Dimmable LED desk lamp with five brightness levels, flexible neck and USB charging port", 21.99, 60),
    ("Home & Kitchen", "Air Fryer 4L", "Digital air fryer that cooks crispy food with little or no oil, with preset cooking modes", 74.99, 20),
    # --- Books ---
    ("Books", "Clean Code Handbook", "A practical guide to writing readable, maintainable software with real-world refactoring examples", 34.99, 30),
    ("Books", "Python Crash Course", "Hands-on beginner-friendly introduction to Python programming through three practical projects", 29.99, 40),
    ("Books", "Atomic Habits Style Self-Help Guide", "Practical strategies for building good habits, breaking bad ones and improving a little every day", 16.99, 70),
    ("Books", "Introduction to Algorithms Workbook", "Exercises and worked solutions covering sorting, graphs, dynamic programming and complexity analysis", 44.99, 20),
    ("Books", "The Startup Playbook", "Stories and lessons from founders on building products, finding customers and raising funding", 18.99, 35),
    ("Books", "World Atlas Illustrated", "Full-colour atlas with detailed maps, flags and facts for every country", 31.99, 25),
    # --- Sports & Outdoors ---
    ("Sports & Outdoors", "Yoga Mat Non-Slip", "6 mm thick non-slip yoga mat with carrying strap, ideal for yoga, pilates and stretching", 21.99, 80),
    ("Sports & Outdoors", "Adjustable Dumbbell Set", "Pair of adjustable dumbbells for home workouts, from 2 kg to 12 kg each", 89.99, 15),
    ("Sports & Outdoors", "Running Shoes Lightweight", "Breathable cushioned running shoes with grippy sole for road and treadmill running", 64.99, 35),
    ("Sports & Outdoors", "Resistance Bands Set", "Five latex resistance bands of different strengths for strength training and rehab", 14.99, 90),
    ("Sports & Outdoors", "Camping Backpack 40L", "Water-resistant 40 litre hiking backpack with padded straps and rain cover", 49.99, 25),
    ("Sports & Outdoors", "Skipping Rope Speed", "Adjustable speed jump rope with ball bearings and foam handles for cardio workouts", 9.99, 100),
    ("Sports & Outdoors", "Badminton Racket Pair", "Two lightweight graphite badminton rackets with shuttlecocks and a carry bag", 28.99, 30),
    # --- Beauty & Personal Care ---
    ("Beauty & Personal Care", "Vitamin C Face Serum", "Brightening vitamin C serum with hyaluronic acid that evens skin tone and boosts glow", 18.99, 60),
    ("Beauty & Personal Care", "Hydrating Moisturizer SPF 30", "Lightweight daily face moisturizer with SPF 30 sun protection for all skin types", 15.99, 70),
    ("Beauty & Personal Care", "Electric Beard Trimmer", "Cordless rechargeable beard trimmer with adjustable length settings and waterproof body", 24.99, 40),
    ("Beauty & Personal Care", "Herbal Shampoo 500ml", "Sulfate-free herbal shampoo that gently cleanses and strengthens hair", 11.99, 85),
    ("Beauty & Personal Care", "Lip Balm Pack of 4", "Moisturizing lip balms with shea butter and natural fruit flavours", 7.99, 120),
    # --- Toys & Games ---
    ("Toys & Games", "Building Blocks 500 Pieces", "Colourful interlocking building blocks set that encourages creativity for ages 5 and up", 27.99, 40),
    ("Toys & Games", "Classic Chess Set Wooden", "Handcrafted wooden chess set with folding board and felt-bottomed pieces", 23.99, 30),
    ("Toys & Games", "Jigsaw Puzzle 1000 Pieces", "Scenic landscape jigsaw puzzle with sturdy, precisely cut pieces", 13.99, 50),
    ("Toys & Games", "Remote Control Car", "Rechargeable off-road RC car with 2.4GHz remote and shock-absorbing tyres", 36.99, 25),
    ("Toys & Games", "Family Board Game Night", "Strategy and trivia board game for 2 to 6 players, fun for the whole family", 29.99, 35),
    # --- Men's / Women's Clothing ---
    ("Men'S Clothing", "Men'S Formal Cotton Shirt", "Wrinkle-resistant slim-fit cotton shirt suited to office and formal occasions", 32.99, 45),
    ("Men'S Clothing", "Men'S Running Shorts", "Quick-dry lightweight shorts with zip pocket for running and gym sessions", 18.99, 60),
    ("Men'S Clothing", "Men'S Winter Jacket", "Warm padded winter jacket with water-repellent shell and fleece lining", 79.99, 20),
    ("Women'S Clothing", "Women'S Cotton Kurti", "Comfortable printed cotton kurti with three-quarter sleeves for everyday wear", 22.99, 50),
    ("Women'S Clothing", "Women'S Wool Cardigan", "Soft knitted cardigan with button front, perfect for layering in cooler weather", 38.99, 30),
    ("Women'S Clothing", "Women'S Athletic Sports Bra", "Medium-support breathable sports bra with moisture-wicking fabric", 19.99, 55),
    # --- Accessories ---
    ("Accessories", "Leather Wallet Bifold", "Genuine leather bifold wallet with RFID protection and multiple card slots", 22.99, 70),
    ("Accessories", "Polarized Sunglasses", "UV400 polarized sunglasses with lightweight durable frame", 19.99, 60),
    ("Accessories", "Canvas Backpack Laptop 15 inch", "Everyday canvas backpack with padded laptop compartment and multiple pockets", 39.99, 40),
    ("Accessories", "Analog Wrist Watch Classic", "Minimalist stainless-steel analog watch with leather strap and date window", 54.99, 25),
]


def seed_more_products():
    print("Adding extended catalog...")
    added = 0
    for category_name, name, description, price, stock in CATALOG:
        if db.query(Product).filter(Product.name == name).first():
            continue  # idempotent: safe to run again
        category = get_or_create_category(category_name, f"{category_name} products")
        db.add(Product(
            name=name,
            description=description,
            price=price,
            stock_quantity=stock,
            image_url="https://placehold.co/300x300?text=" + quote_plus(name),
            category_id=category.id,
        ))
        added += 1
    db.commit()
    print(f"Added {added} new products ({len(CATALOG) - added} already existed).")


if __name__ == "__main__":
    seed_from_fake_store_api()
    seed_manual_products()
    seed_more_products()
    db.close()
    print("Seeding complete!")