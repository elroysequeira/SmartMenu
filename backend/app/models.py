"""SQLModel and Pydantic models for the application."""
from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal


# ============================================================================
# Database Models (SQLModel)
# ============================================================================

class Restaurant(SQLModel, table=True):
    """Restaurant table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MenuItem(SQLModel, table=True):
    """Menu item table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurant_id: int = Field(foreign_key="restaurant.id")
    name: str
    description: Optional[str] = None
    category: str  # e.g., "starters", "mains", "desserts", "beverages"
    price: Decimal = Field(decimal_places=2)
    available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Modifier(SQLModel, table=True):
    """Menu item modifier table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurant_id: int = Field(foreign_key="restaurant.id")
    name: str
    price: Decimal = Field(decimal_places=2, default=Decimal("0.00"))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MenuItemModifier(SQLModel, table=True):
    """Junction table for menu items and modifiers."""
    id: Optional[int] = Field(default=None, primary_key=True)
    menu_item_id: int = Field(foreign_key="menuitem.id")
    modifier_id: int = Field(foreign_key="modifier.id")


class GuestSession(SQLModel, table=True):
    """Guest session table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    restaurant_slug: str
    table_id: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Order(SQLModel, table=True):
    """Order table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: UUID = Field(foreign_key="guestsession.session_id", index=True)
    table_id: str
    status: str = Field(default="pending")  # pending, completed, cancelled
    subtotal: Decimal = Field(decimal_places=2)
    tax: Decimal = Field(decimal_places=2)
    total_amount: Decimal = Field(decimal_places=2)
    payment_method: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrderItem(SQLModel, table=True):
    """Order item table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    menu_item_id: int = Field(foreign_key="menuitem.id")
    quantity: int
    unit_price: Decimal = Field(decimal_places=2)
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderItemModifier(SQLModel, table=True):
    """Order item modifier table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    order_item_id: int = Field(foreign_key="orderitem.id")
    modifier_id: int = Field(foreign_key="modifier.id")
    price: Decimal = Field(decimal_places=2)


# ============================================================================
# Pydantic Models for API
# ============================================================================

class SessionCreate(SQLModel):
    """Request model for creating a session."""
    restaurant_slug: str
    table_id: str


class SessionResponse(SQLModel):
    """Response model for session."""
    session_id: UUID
    expires_at: datetime


class OrderItemCreate(SQLModel):
    """Request model for order item."""
    item_id: int
    quantity: int
    modifier_ids: Optional[List[int]] = None
    note: Optional[str] = None


class PaymentInfo(SQLModel):
    """Payment information."""
    method: str


class OrderCreate(SQLModel):
    """Request model for creating an order."""
    session_id: UUID
    table_id: str
    items: List[OrderItemCreate]
    payment: PaymentInfo


class OrderUpdate(SQLModel):
    """Request model for updating an order."""
    items: List[OrderItemCreate]


class OrderResponse(SQLModel):
    """Response model for order."""
    order_id: int
    status: str
    total_amount: Decimal


class OrderDetailResponse(SQLModel):
    """Detailed order response for admin listing."""
    order_id: int
    status: str
    table_id: str
    subtotal: Decimal
    tax: Decimal
    total_amount: Decimal
    payment_method: str
    created_at: datetime
    items: List[dict]  # Simplified for JSON response


class MenuItemResponse(SQLModel):
    """Response model for menu item."""
    id: int
    name: str
    description: Optional[str]
    category: str
    price: Decimal
    available: bool
    modifiers: Optional[List[dict]] = None


class MenuResponse(SQLModel):
    """Response model for restaurant menu."""
    restaurant: dict
    items: List[MenuItemResponse]

