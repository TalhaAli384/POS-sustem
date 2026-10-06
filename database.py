"""SQLite schema, connection management, and seed data for the POS system."""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "pos.db"
RECEIPTS_DIR = BASE_DIR / "receipts"
RECEIPTS_DIR.mkdir(exist_ok=True)

_connection = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    pin TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('cashier', 'manager', 'admin')),
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    name TEXT NOT NULL,
    price REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS modifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price_delta REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS item_modifiers (
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    modifier_id INTEGER NOT NULL REFERENCES modifiers(id) ON DELETE CASCADE,
    PRIMARY KEY (menu_item_id, modifier_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_type TEXT NOT NULL DEFAULT 'Dine-In',
    status TEXT NOT NULL DEFAULT 'draft',
    subtotal REAL NOT NULL DEFAULT 0,
    tax REAL NOT NULL DEFAULT 0,
    discount_type TEXT,
    discount_value REAL NOT NULL DEFAULT 0,
    discount_amount REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    payment_method TEXT,
    tendered REAL,
    change_due REAL,
    cashier_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
    item_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS order_item_modifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    modifier_name TEXT NOT NULL,
    price_delta REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def get_db():
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA foreign_keys = ON")
    return _connection


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
    _seed(db)


def _seed(db):
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) AS n FROM settings")
    if cur.fetchone()["n"] == 0:
        db.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            [
                ("restaurant_name", "Big Byte Burgers"),
                ("currency_symbol", "$"),
                ("tax_rate", "0.0825"),
            ],
        )

    cur.execute("SELECT COUNT(*) AS n FROM users")
    if cur.fetchone()["n"] == 0:
        db.executemany(
            "INSERT INTO users (name, pin, role, active) VALUES (?, ?, ?, 1)",
            [
                ("Owner Admin", "1234", "admin"),
                ("Shift Manager", "2580", "manager"),
                ("John", "1111", "cashier"),
                ("Amy", "2222", "cashier"),
            ],
        )

    cur.execute("SELECT COUNT(*) AS n FROM categories")
    if cur.fetchone()["n"] == 0:
        categories = ["Burgers", "Chicken", "Sides", "Drinks", "Desserts"]
        for i, name in enumerate(categories):
            cur.execute(
                "INSERT INTO categories (name, sort_order) VALUES (?, ?)", (name, i)
            )
        db.commit()

        cat_ids = {
            row["name"]: row["id"]
            for row in cur.execute("SELECT id, name FROM categories")
        }

        items = [
            ("Burgers", "Classic Cheeseburger", 5.49),
            ("Burgers", "Double Bacon Burger", 7.99),
            ("Burgers", "Veggie Burger", 6.29),
            ("Burgers", "Big Byte Deluxe", 8.49),
            ("Chicken", "Crispy Chicken Sandwich", 6.49),
            ("Chicken", "Spicy Chicken Sandwich", 6.79),
            ("Chicken", "Chicken Nuggets (10pc)", 5.99),
            ("Chicken", "Chicken Tenders (3pc)", 6.49),
            ("Sides", "French Fries", 2.99),
            ("Sides", "Curly Fries", 3.49),
            ("Sides", "Onion Rings", 3.79),
            ("Sides", "Side Salad", 3.29),
            ("Drinks", "Fountain Soda", 1.99),
            ("Drinks", "Iced Tea", 1.99),
            ("Drinks", "Bottled Water", 1.49),
            ("Drinks", "Milkshake", 3.99),
            ("Desserts", "Soft Serve Cone", 1.99),
            ("Desserts", "Apple Pie", 2.49),
            ("Desserts", "Chocolate Brownie", 2.99),
        ]
        for i, (cat, name, price) in enumerate(items):
            cur.execute(
                "INSERT INTO menu_items (category_id, name, price, active, sort_order) "
                "VALUES (?, ?, ?, 1, ?)",
                (cat_ids[cat], name, price, i),
            )

        modifiers = [
            ("No Onions", 0.0),
            ("No Pickles", 0.0),
            ("Extra Cheese", 0.75),
            ("Extra Patty", 1.50),
            ("Add Bacon", 1.25),
            ("Make it Spicy", 0.0),
            ("Large Size", 1.50),
        ]
        cur.executemany(
            "INSERT INTO modifiers (name, price_delta) VALUES (?, ?)", modifiers
        )
        db.commit()

        mod_ids = {
            row["name"]: row["id"]
            for row in cur.execute("SELECT id, name FROM modifiers")
        }
        item_ids = {
            row["name"]: row["id"]
            for row in cur.execute("SELECT id, name FROM menu_items")
        }

        burger_mods = ["No Onions", "No Pickles", "Extra Cheese", "Extra Patty", "Add Bacon"]
        chicken_mods = ["No Onions", "No Pickles", "Extra Cheese", "Make it Spicy"]
        drink_mods = ["Large Size"]

        for item_name in ["Classic Cheeseburger", "Double Bacon Burger", "Veggie Burger", "Big Byte Deluxe"]:
            for mod_name in burger_mods:
                cur.execute(
                    "INSERT OR IGNORE INTO item_modifiers (menu_item_id, modifier_id) VALUES (?, ?)",
                    (item_ids[item_name], mod_ids[mod_name]),
                )
        for item_name in ["Crispy Chicken Sandwich", "Spicy Chicken Sandwich"]:
            for mod_name in chicken_mods:
                cur.execute(
                    "INSERT OR IGNORE INTO item_modifiers (menu_item_id, modifier_id) VALUES (?, ?)",
                    (item_ids[item_name], mod_ids[mod_name]),
                )
        for item_name in ["Fountain Soda", "Iced Tea", "Milkshake"]:
            for mod_name in drink_mods:
                cur.execute(
                    "INSERT OR IGNORE INTO item_modifiers (menu_item_id, modifier_id) VALUES (?, ?)",
                    (item_ids[item_name], mod_ids[mod_name]),
                )

    db.commit()
