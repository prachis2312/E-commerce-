import requests
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
            "image_url": "https://via.placeholder.com/300?text=Gaming+Mouse",
            "category": "Electronics"
        },
        {
            "name": "Mechanical Keyboard",
            "description": "Compact mechanical keyboard with blue switches, ideal for typing and gaming",
            "price": 79.99,
            "stock_quantity": 25,
            "image_url": "https://via.placeholder.com/300?text=Keyboard",
            "category": "Electronics"
        },
        {
            "name": "Noise Cancelling Headphones",
            "description": "Over-ear wireless headphones with active noise cancellation and 30-hour battery life",
            "price": 129.99,
            "stock_quantity": 20,
            "image_url": "https://via.placeholder.com/300?text=Headphones",
            "category": "Electronics"
        },
        {
            "name": "Portable Bluetooth Speaker",
            "description": "Compact waterproof speaker with deep bass and 12-hour playtime",
            "price": 34.99,
            "stock_quantity": 40,
            "image_url": "https://via.placeholder.com/300?text=Speaker",
            "category": "Electronics"
        },
        {
            "name": "Smartwatch Fitness Tracker",
            "description": "Tracks heart rate, sleep, and steps with a 7-day battery life",
            "price": 59.99,
            "stock_quantity": 35,
            "image_url": "https://via.placeholder.com/300?text=Smartwatch",
            "category": "Electronics"
        },
        {
            "name": "Men'S Cotton Hoodie",
            "description": "Soft cotton-blend hoodie, relaxed fit, available in multiple colors",
            "price": 29.99,
            "stock_quantity": 60,
            "image_url": "https://via.placeholder.com/300?text=Hoodie",
            "category": "Men'S Clothing"
        },
        {
            "name": "Men'S Slim Fit Jeans",
            "description": "Stretchable slim-fit denim jeans, mid-rise, everyday wear",
            "price": 39.99,
            "stock_quantity": 45,
            "image_url": "https://via.placeholder.com/300?text=Jeans",
            "category": "Men'S Clothing"
        },
        {
            "name": "Men'S Casual Sneakers",
            "description": "Lightweight breathable sneakers, ideal for daily casual wear",
            "price": 49.99,
            "stock_quantity": 30,
            "image_url": "https://via.placeholder.com/300?text=Sneakers",
            "category": "Men'S Clothing"
        },
        {
            "name": "Women'S Floral Summer Dress",
            "description": "Lightweight floral print dress, perfect for casual summer outings",
            "price": 34.99,
            "stock_quantity": 40,
            "image_url": "https://via.placeholder.com/300?text=Summer+Dress",
            "category": "Women'S Clothing"
        },
        {
            "name": "Women'S Denim Jacket",
            "description": "Classic denim jacket with button closure, versatile everyday layering piece",
            "price": 44.99,
            "stock_quantity": 25,
            "image_url": "https://via.placeholder.com/300?text=Denim+Jacket",
            "category": "Women'S Clothing"
        },
        {
            "name": "Women'S Yoga Leggings",
            "description": "High-waisted stretch leggings designed for yoga and everyday activewear",
            "price": 24.99,
            "stock_quantity": 55,
            "image_url": "https://via.placeholder.com/300?text=Leggings",
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

if __name__ == "__main__":
    seed_from_fake_store_api()
    seed_manual_products()
    db.close()
    print("Seeding complete!")