"""Initialize database and seed menu data."""
import json
from pathlib import Path
from decimal import Decimal
from sqlmodel import Session, select
from app.db import engine, create_db_and_tables
from app.models import Restaurant, MenuItem, Modifier, MenuItemModifier

# Path to seed file
SEED_FILE = Path(__file__).parent / "seed" / "menu.json"


def seed_database():
    """Load menu data from JSON and populate database."""
    # Read seed file
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        menu_data = json.load(f)
    
    with Session(engine) as session:
        # Create or get restaurant
        restaurant_data = menu_data["restaurant"]
        statement = select(Restaurant).where(Restaurant.slug == restaurant_data["slug"])
        restaurant = session.exec(statement).first()
        
        if not restaurant:
            restaurant = Restaurant(
                slug=restaurant_data["slug"],
                name=restaurant_data["name"]
            )
            session.add(restaurant)
            session.commit()
            session.refresh(restaurant)
            print(f"Created restaurant: {restaurant.name}")
        else:
            print(f"Restaurant already exists: {restaurant.name}")
        
        # Clear existing menu items and modifiers for this restaurant
        # (for re-seeding)
        existing_items = session.exec(
            select(MenuItem).where(MenuItem.restaurant_id == restaurant.id)
        ).all()
        for item in existing_items:
            # Delete menu item modifiers first
            item_mods = session.exec(
                select(MenuItemModifier).where(MenuItemModifier.menu_item_id == item.id)
            ).all()
            for item_mod in item_mods:
                session.delete(item_mod)
            session.delete(item)
        
        existing_modifiers = session.exec(
            select(Modifier).where(Modifier.restaurant_id == restaurant.id)
        ).all()
        for mod in existing_modifiers:
            session.delete(mod)
        
        session.commit()
        
        # Create modifiers with explicit IDs from JSON
        modifiers_map = {}
        for mod_data in menu_data["modifiers"]:
            modifier = Modifier(
                id=mod_data["id"],  # Use ID from JSON
                restaurant_id=restaurant.id,
                name=mod_data["name"],
                price=Decimal(str(mod_data["price"]))
            )
            session.add(modifier)
            session.flush()
            modifiers_map[mod_data["id"]] = mod_data["id"]
            print(f"Created modifier: {modifier.name} (ID: {modifier.id})")
        
        # Create menu items with explicit IDs from JSON
        for item_data in menu_data["items"]:
            menu_item = MenuItem(
                id=item_data["id"],  # Use ID from JSON
                restaurant_id=restaurant.id,
                name=item_data["name"],
                description=item_data.get("description"),
                category=item_data["category"],
                price=Decimal(str(item_data["price"])),
                available=True
            )
            session.add(menu_item)
            session.flush()
            print(f"Created menu item: {menu_item.name} (ID: {menu_item.id})")
            
            # Link modifiers to menu item
            for mod_id in item_data.get("modifier_ids", []):
                if mod_id in modifiers_map:
                    item_modifier = MenuItemModifier(
                        menu_item_id=item_data["id"],
                        modifier_id=mod_id
                    )
                    session.add(item_modifier)
        
        session.commit()
        print("\nDatabase seeded successfully!")


if __name__ == "__main__":
    print("Creating database tables...")
    create_db_and_tables()
    print("Database tables created.\n")
    
    print("Seeding database from menu.json...")
    seed_database()
    print("\nInitialization complete!")

