import sqlite3
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")
DB = "inventory.db"
LOW_STOCK = 10


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            price REAL NOT NULL CHECK(price >= 0))""")


QUERY = """SELECT p.id, p.product_id, p.name, c.name AS category, p.quantity, p.price
           FROM products p JOIN categories c ON c.id = p.category_id"""


def row(r):
    d = dict(r)
    d["low_stock"] = d["quantity"] <= LOW_STOCK
    return d


def validate(data, partial=False):
    """Return (clean, error). With partial=True only quantity/price are checked."""
    clean = {}
    if not partial:
        for f in ("product_id", "name", "category"):
            v = str(data.get(f, "")).strip()
            if not v:
                return None, f"{f.replace('_', ' ').title()} is required"
            clean[f] = v
    for f in ("quantity", "price"):
        if f in data or not partial:
            try:
                v = int(data[f]) if f == "quantity" else float(data[f])
            except (KeyError, ValueError, TypeError):
                return None, f"{f.title()} must be a number"
            if v < 0:
                return None, f"{f.title()} cannot be negative"
            clean[f] = v
    return clean, None


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/products")
def list_products():
    q = request.args.get("q", "").strip()
    sql, args = QUERY, []
    if q:
        sql += " WHERE p.product_id LIKE ? OR p.name LIKE ? OR c.name LIKE ?"
        args = [f"%{q}%"] * 3
    with db() as c:
        rows = c.execute(sql + " ORDER BY p.id DESC", args).fetchall()
    return jsonify([row(r) for r in rows])


@app.post("/api/products")
def add_product():
    data, err = validate(request.get_json(silent=True) or {})
    if err:
        return jsonify(error=err), 400
    with db() as c:
        if c.execute("SELECT 1 FROM products WHERE product_id=?", (data["product_id"],)).fetchone():
            return jsonify(error="Product ID already exists"), 409
        c.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (data["category"],))
        cat = c.execute("SELECT id FROM categories WHERE name=?", (data["category"],)).fetchone()["id"]
        c.execute("INSERT INTO products(product_id,name,category_id,quantity,price) VALUES (?,?,?,?,?)",
                  (data["product_id"], data["name"], cat, data["quantity"], data["price"]))
    return jsonify(message="Product added"), 201


@app.put("/api/products/<int:pid>")
def update_product(pid):
    body = request.get_json(silent=True) or {}
    data, err = validate(body, partial=True)
    if err:
        return jsonify(error=err), 400
    if not data:
        return jsonify(error="Nothing to update"), 400
    with db() as c:
        cur = c.execute("SELECT quantity FROM products WHERE id=?", (pid,)).fetchone()
        if not cur:
            return jsonify(error="Product not found"), 404
        sets = ", ".join(f"{k}=?" for k in data)
        c.execute(f"UPDATE products SET {sets} WHERE id=?", [*data.values(), pid])
    return jsonify(message="Product updated")


@app.delete("/api/products/<int:pid>")
def delete_product(pid):
    with db() as c:
        cur = c.execute("DELETE FROM products WHERE id=?", (pid,))
    if cur.rowcount == 0:
        return jsonify(error="Product not found"), 404
    return jsonify(message="Product deleted")


init_db()
if __name__ == "__main__":
    app.run(debug=True)
