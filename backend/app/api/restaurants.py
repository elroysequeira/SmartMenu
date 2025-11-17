"""Restaurant menu endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models import Restaurant, MenuItem, Modifier, MenuItemModifier, MenuItemResponse, MenuResponse

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.get("/{slug}/menu", response_model=MenuResponse)
def get_restaurant_menu(slug: str, session: Session = Depends(get_session)):
    """
    Get the menu for a restaurant by slug.
    
    Returns all menu items with their available modifiers.
    """
    # Get restaurant
    statement = select(Restaurant).where(Restaurant.slug == slug)
    restaurant = session.exec(statement).first()
    
    if not restaurant:
        raise HTTPException(status_code=404, detail=f"Restaurant '{slug}' not found")
    
    # Get menu items
    statement = select(MenuItem).where(
        MenuItem.restaurant_id == restaurant.id,
        MenuItem.available == True
    ).order_by(MenuItem.category, MenuItem.name)
    menu_items = session.exec(statement).all()
    
    # Get all modifiers for this restaurant
    mod_statement = select(Modifier).where(Modifier.restaurant_id == restaurant.id)
    all_modifiers = session.exec(mod_statement).all()
    modifiers_dict = {mod.id: mod for mod in all_modifiers}
    
    # Get menu item modifiers mapping
    item_mod_statement = select(MenuItemModifier)
    item_modifiers = session.exec(item_mod_statement).all()
    item_mod_map = {}
    for item_mod in item_modifiers:
        if item_mod.menu_item_id not in item_mod_map:
            item_mod_map[item_mod.menu_item_id] = []
        item_mod_map[item_mod.menu_item_id].append(item_mod.modifier_id)
    
    # Build response
    items_response = []
    for item in menu_items:
        modifier_list = None
        if item.id in item_mod_map:
            modifier_list = [
                {
                    "id": mod_id,
                    "name": modifiers_dict[mod_id].name,
                    "price": float(modifiers_dict[mod_id].price)
                }
                for mod_id in item_mod_map[item.id]
            ]
        
        items_response.append(MenuItemResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            category=item.category,
            price=item.price,
            available=item.available,
            modifiers=modifier_list
        ))
    
    return MenuResponse(
        restaurant={
            "id": restaurant.id,
            "slug": restaurant.slug,
            "name": restaurant.name
        },
        items=items_response
    )

