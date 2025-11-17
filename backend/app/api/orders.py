"""Order management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
from app.db import get_session
from app.models import (
    OrderCreate, OrderUpdate, OrderResponse, OrderDetailResponse,
    Order, GuestSession
)
from app.services import calculate_order_total, create_order_items, get_order_details

router = APIRouter(prefix="/api/orders", tags=["orders"])

# Simple admin key (in production, use environment variable or proper auth)
ADMIN_KEY = "dev-admin-key"


def verify_admin_key(admin_key: Optional[str] = Query(None)):
    """Verify admin key for protected endpoints."""
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return admin_key


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(order_data: OrderCreate, session: Session = Depends(get_session)):
    """
    Create a new order.
    
    Validates session, calculates totals including tax (5%), and creates order items.
    """
    # Verify session exists and is valid
    statement = select(GuestSession).where(
        GuestSession.session_id == order_data.session_id,
        GuestSession.expires_at > datetime.utcnow()
    )
    guest_session = session.exec(statement).first()
    
    if not guest_session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Verify table_id matches
    if guest_session.table_id != order_data.table_id:
        raise HTTPException(status_code=400, detail="Table ID mismatch")
    
    # Calculate totals
    try:
        subtotal, tax, total_amount = calculate_order_total(session, [
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "modifier_ids": item.modifier_ids or []
            }
            for item in order_data.items
        ])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create order
    new_order = Order(
        session_id=order_data.session_id,
        table_id=order_data.table_id,
        status="pending",
        subtotal=subtotal,
        tax=tax,
        total_amount=total_amount,
        payment_method=order_data.payment.method
    )
    session.add(new_order)
    session.commit()
    session.refresh(new_order)
    
    # Create order items
    try:
        create_order_items(session, new_order.id, [
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "modifier_ids": item.modifier_ids or [],
                "note": item.note
            }
            for item in order_data.items
        ])
        session.commit()
    except ValueError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    return OrderResponse(
        order_id=new_order.id,
        status=new_order.status,
        total_amount=new_order.total_amount
    )


@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    session: Session = Depends(get_session)
):
    """
    Append items to an existing pending order.
    
    Only allows updates to orders with status "pending".
    Recalculates totals including new items.
    """
    # Get existing order
    existing_order = session.get(Order, order_id)
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if existing_order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update order with status '{existing_order.status}'"
        )
    
    # Calculate new totals
    try:
        subtotal, tax, total_amount = calculate_order_total(session, [
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "modifier_ids": item.modifier_ids or []
            }
            for item in order_update.items
        ], existing_order=existing_order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Update order totals
    existing_order.subtotal = subtotal
    existing_order.tax = tax
    existing_order.total_amount = total_amount
    existing_order.updated_at = datetime.utcnow()
    
    # Create new order items
    try:
        create_order_items(session, order_id, [
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "modifier_ids": item.modifier_ids or [],
                "note": item.note
            }
            for item in order_update.items
        ])
        session.commit()
    except ValueError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    return OrderResponse(
        order_id=existing_order.id,
        status=existing_order.status,
        total_amount=existing_order.total_amount
    )


@router.get("", response_model=list[OrderDetailResponse])
def list_orders(
    admin_key: str = Depends(verify_admin_key),
    status: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """
    List all orders (admin only).
    
    Supports optional filtering by status (pending, completed, cancelled).
    """
    statement = select(Order).order_by(Order.created_at.desc())
    
    if status:
        statement = statement.where(Order.status == status)
    
    orders = session.exec(statement).all()
    
    # Get details for each order
    orders_response = []
    for order in orders:
        order_details = get_order_details(session, order.id)
        if order_details:
            orders_response.append(OrderDetailResponse(**order_details))
    
    return orders_response

