"""FastAPI application main file."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import restaurants, sessions, orders
from app.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed in the future)


# Create FastAPI app
app = FastAPI(
    title="Smart Menu MVP Backend",
    description="Backend API for QR-menu MVP system",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(restaurants.router)
app.include_router(sessions.router)
app.include_router(orders.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Smart Menu MVP Backend API",
        "docs": "/docs",
        "version": "1.0.0"
    }

