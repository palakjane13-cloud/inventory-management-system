# Stockroom - Inventory Management System (Aim 6)

Stack: HTML/CSS/JS (Fetch API) + Python Flask + SQLite.

## Run
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/products?q= | List / search by ID, name, category |
| POST | /api/products | Add product |
| PUT | /api/products/<id> | Update quantity / price |
| DELETE | /api/products/<id> | Delete product |

Schema: `categories(id, name)` 1-to-many `products(id, product_id UNIQUE, name, category_id, quantity>=0, price>=0)`.
Low-stock threshold: 10 (set LOW_STOCK in app.py).
