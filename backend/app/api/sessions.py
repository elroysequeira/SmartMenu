"""Guest session endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.db import get_session
from app.models import SessionCreate, SessionResponse, GuestSession

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(session_data: SessionCreate, session: Session = Depends(get_session)):
    """
    Create or return an existing guest session for a restaurant and table.
    
    Sessions expire after 2 hours. If a valid session exists, it is returned.
    Otherwise, a new session is created.
    """
    # Check for existing valid session
    expires_at = datetime.utcnow() + timedelta(hours=2)
    statement = select(GuestSession).where(
        GuestSession.restaurant_slug == session_data.restaurant_slug,
        GuestSession.table_id == session_data.table_id,
        GuestSession.expires_at > datetime.utcnow()
    )
    existing_session = session.exec(statement).first()
    
    if existing_session:
        return SessionResponse(
            session_id=existing_session.session_id,
            expires_at=existing_session.expires_at
        )
    
    # Create new session
    new_session = GuestSession(
        restaurant_slug=session_data.restaurant_slug,
        table_id=session_data.table_id,
        expires_at=expires_at
    )
    session.add(new_session)
    session.commit()
    session.refresh(new_session)
    
    return SessionResponse(
        session_id=new_session.session_id,
        expires_at=new_session.expires_at
    )

