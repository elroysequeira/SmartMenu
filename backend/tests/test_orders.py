"""Unit tests for order endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from datetime import datetime, timedelta
from app.main import app
from app.db import get_session
from app.models import Restaurant, MenuItem, Modifier, MenuItemModifier, GuestSession


# Shared in-memory database engine
test_engine = create_engine("sqlite:///:memory:", echo=False)


@pytest.fixture(scope="function")
def test_session():
    """Create a test database session with test data."""
    SQLModel.metadata.create_all(test_engine)
    
    with Session(test_engine) as session:
        # Create test restaurant
        restaurant = Restaurant(
            slug="test-restaurant",
            name="Test Restaurant"
        )
        session.add(restaurant)
        session.commit()
        session.refresh(restaurant)
        
        # Create test modifiers
        modifier1 = Modifier(
            restaurant_id=restaurant.id,
            name="Extra Cheese",
            price=2.50
        )
        modifier2 = Modifier(
            restaurant_id=restaurant.id,
            name="Add Bacon",
            price=3.00
        )
        session.add(modifier1)
        session.add(modifier2)
        session.commit()
        session.refresh(modifier1)
        session.refresh(modifier2)
        
        # Create test menu items
        item1 = MenuItem(
            restaurant_id=restaurant.id,
            name="Test Burger",
            category="mains",
            price=15.00
        )
        item2 = MenuItem(
            restaurant_id=restaurant.id,
            name="Test Salad",
            category="starters",
            price=10.00
        )
        session.add(item1)
        session.add(item2)
        session.commit()
        session.refresh(item1)
        session.refresh(item2)
        
        # Link modifiers to items
        item_mod1 = MenuItemModifier(
            menu_item_id=item1.id,
            modifier_id=modifier1.id
        )
        item_mod2 = MenuItemModifier(
            menu_item_id=item1.id,
            modifier_id=modifier2.id
        )
        session.add(item_mod1)
        session.add(item_mod2)
        session.commit()
        
        # Create test session
        session_obj = GuestSession(
            restaurant_slug="test-restaurant",
            table_id="5",
            expires_at=datetime.utcnow() + timedelta(hours=2)
        )
        session.add(session_obj)
        session.commit()
        session.refresh(session_obj)
        
        yield session, session_obj.session_id, item1.id, item2.id, modifier1.id
    
    # Clean up
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client(test_session):
    """Create test client with test database."""
    session, session_id, item1_id, item2_id, mod1_id = test_session
    
    def override_get_session():
        with Session(test_engine) as db_session:
            yield db_session
    
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client, session_id, item1_id, item2_id, mod1_id
    app.dependency_overrides.clear()


def test_create_order(client):
    """Test creating an order via POST /api/orders."""
    client_obj, session_id, item1_id, item2_id, mod1_id = client
    
    # Create order
    order_data = {
        "session_id": str(session_id),
        "table_id": "5",
        "items": [
            {"item_id": item1_id, "quantity": 1, "modifier_ids": [mod1_id]},
            {"item_id": item2_id, "quantity": 2}
        ],
        "payment": {"method": "cash"}
    }
    
    response = client_obj.post("/api/orders", json=order_data)
    
    # Assertions
    assert response.status_code == 201
    data = response.json()
    
    assert "order_id" in data
    assert data["status"] == "pending"
    assert "total_amount" in data
    
    # Calculate expected total:
    # Item 1: 15.00 + modifier 2.50 = 17.50
    # Item 2: 10.00 * 2 = 20.00
    # Subtotal: 37.50
    # Tax (5%): 1.875
    # Total: 39.375 -> 39.38 (rounded)
    expected_total = round(39.375, 2)
    assert abs(float(data["total_amount"]) - expected_total) < 0.01

