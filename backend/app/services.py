"""Business logic and helper functions."""
from decimal import Decimal
from typing import List, Dict, Optional
from sqlmodel import Session, select
from app.models import (
    MenuItem, Modifier, OrderItem, OrderItemModifier,
    Order, GuestSession
)

TAX_RATE = Decimal("0.05")  # 5% tax


def calculate_order_total(
    session: Session,
    items: List[Dict],
    existing_order: Optional[Order] = None
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Calculate order totals (subtotal, tax, total_amount).
    
    Args:
        session: Database session
        items: List of order items with item_id, quantity, modifier_ids
        existing_order: Optional existing order to add to
        
    Returns:
        Tuple of (subtotal, tax, total_amount)
    """
    subtotal = existing_order.subtotal if existing_order else Decimal("0.00")
    
    for item_data in items:
        item_id = item_data["item_id"]
        quantity = item_data["quantity"]
        modifier_ids = item_data.get("modifier_ids", [])
        
        # Get menu item
        menu_item = session.get(MenuItem, item_id)
        if not menu_item:
            raise ValueError(f"Menu item {item_id} not found")
        
        # Calculate item total
        item_subtotal = menu_item.price * quantity
        subtotal += item_subtotal
        
        # Add modifier prices
        if modifier_ids:
            for mod_id in modifier_ids:
                modifier = session.get(Modifier, mod_id)
                if not modifier:
                    raise ValueError(f"Modifier {mod_id} not found")
                subtotal += modifier.price * quantity
    
    # Calculate tax and total
    tax = subtotal * TAX_RATE
    total_amount = subtotal + tax
    
    return subtotal, tax, total_amount


def create_order_items(
    session: Session,
    order_id: int,
    items: List[Dict]
) -> List[OrderItem]:
    """
    Create order items and their modifiers in the database.
    
    Args:
        session: Database session
        order_id: Order ID
        items: List of order items with item_id, quantity, modifier_ids, note
        
    Returns:
        List of created OrderItem objects
    """
    order_items = []
    
    for item_data in items:
        item_id = item_data["item_id"]
        quantity = item_data["quantity"]
        modifier_ids = item_data.get("modifier_ids", [])
        note = item_data.get("note")
        
        # Get menu item
        menu_item = session.get(MenuItem, item_id)
        if not menu_item:
            raise ValueError(f"Menu item {item_id} not found")
        
        # Create order item
        order_item = OrderItem(
            order_id=order_id,
            menu_item_id=item_id,
            quantity=quantity,
            unit_price=menu_item.price,
            note=note
        )
        session.add(order_item)
        session.flush()  # Get order_item.id
        
        # Create order item modifiers
        if modifier_ids:
            for mod_id in modifier_ids:
                modifier = session.get(Modifier, mod_id)
                if not modifier:
                    raise ValueError(f"Modifier {mod_id} not found")
                
                order_item_modifier = OrderItemModifier(
                    order_item_id=order_item.id,
                    modifier_id=mod_id,
                    price=modifier.price
                )
                session.add(order_item_modifier)
        
        order_items.append(order_item)
    
    return order_items


def get_order_details(session: Session, order_id: int) -> Dict:
    """
    Get detailed order information including items.
    
    Args:
        session: Database session
        order_id: Order ID
        
    Returns:
        Dictionary with order details and items
    """
    order = session.get(Order, order_id)
    if not order:
        return None
    
    # Get order items
    statement = select(OrderItem).where(OrderItem.order_id == order_id)
    order_items = session.exec(statement).all()
    
    items_data = []
    for order_item in order_items:
        menu_item = session.get(MenuItem, order_item.menu_item_id)
        
        # Get modifiers for this order item
        mod_statement = select(OrderItemModifier).where(
            OrderItemModifier.order_item_id == order_item.id
        )
        order_modifiers = session.exec(mod_statement).all()
        
        modifiers_data = []
        for order_mod in order_modifiers:
            modifier = session.get(Modifier, order_mod.modifier_id)
            modifiers_data.append({
                "id": modifier.id,
                "name": modifier.name,
                "price": float(order_mod.price)
            })
        
        items_data.append({
            "item_id": order_item.menu_item_id,
            "name": menu_item.name,
            "quantity": order_item.quantity,
            "unit_price": float(order_item.unit_price),
            "modifiers": modifiers_data,
            "note": order_item.note
        })
    
    return {
        "order_id": order.id,
        "status": order.status,
        "table_id": order.table_id,
        "subtotal": float(order.subtotal),
        "tax": float(order.tax),
        "total_amount": float(order.total_amount),
        "payment_method": order.payment_method,
        "created_at": order.created_at.isoformat(),
        "items": items_data
    }

