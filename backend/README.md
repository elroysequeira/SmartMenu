# Smart Menu MVP Backend

A FastAPI backend for a QR-menu MVP system. This backend handles restaurant menus, guest sessions, and order management.

## Setup

### 1. Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Unix/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

This will create the SQLite database and seed it with menu data:

```bash
python init_db.py
```

This creates `backend/db.sqlite` and populates it with menu data from `seed/menu.json`.

### 4. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Get Restaurant Menu

```bash
GET /api/restaurants/{slug}/menu
```

Example:
```bash
curl http://localhost:8000/api/restaurants/sunset-bistro/menu
```

### Create Guest Session

```bash
POST /api/sessions
```

Request body:
```json
{
  "restaurant_slug": "sunset-bistro",
  "table_id": "12"
}
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_at": "2024-01-01T12:00:00"
}
```

### Create Order

```bash
POST /api/orders
```

Request body:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "table_id": "12",
  "items": [
    {"item_id": 201, "quantity": 1, "modifier_ids": [2001]},
    {"item_id": 401, "quantity": 2}
  ],
  "payment": {"method": "cash"}
}
```

Response:
```json
{
  "order_id": 1001,
  "status": "pending",
  "total_amount": 520.00
}
```

### Update Order (Append Items)

```bash
PATCH /api/orders/{order_id}
```

Request body:
```json
{
  "items": [
    {"item_id": 301, "quantity": 1}
  ]
}
```

### List Orders (Admin)

```bash
GET /api/orders?admin_key=your-admin-key&status=pending
```

Query parameters:
- `admin_key` (required): Admin authentication key
- `status` (optional): Filter by order status (pending, completed, cancelled)

## Running Tests

```bash
pytest tests/
```

Or with verbose output:
```bash
pytest tests/ -v
```

## Generate QR Codes

Generate QR codes for restaurant tables:

```bash
python scripts/generate_qr.py --restaurant-slug sunset-bistro --tables 10
```

This creates QR code images for tables 1-10, pointing to `https://localhost:3000/r/sunset-bistro/t/{tableId}`.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/                 # API route handlers
│   │   ├── restaurants.py   # Restaurant menu endpoints
│   │   ├── sessions.py      # Guest session endpoints
│   │   └── orders.py        # Order management endpoints
│   ├── models.py            # SQLModel and Pydantic models
│   ├── db.py                # Database session and engine
│   └── services.py          # Business logic (calculations, helpers)
├── seed/
│   └── menu.json            # Menu seed data
├── scripts/
│   └── generate_qr.py       # QR code generation script
├── tests/
│   └── test_orders.py       # Unit tests
├── init_db.py               # Database initialization
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Database

The SQLite database file is created at `backend/db.sqlite`. To reset the database:

1. Delete `backend/db.sqlite`
2. Run `python init_db.py` again

## Notes

- Sessions expire after 2 hours
- Tax is calculated at 5% of subtotal
- Order totals include item prices, modifier prices, and tax
- Admin key is set via environment variable `ADMIN_KEY` (defaults to "dev-admin-key" for development)

