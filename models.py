"""Data access layer: all business logic for orders, menu, staff, and reports."""
from datetime import datetime
from database import get_db

ACTIVE_KDS_STATUSES = ("new", "preparing", "ready")


# ---------------------------------------------------------------- settings --
def get_setting(key, default=None):
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    db = get_db()
    db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    db.commit()


def get_tax_rate():
    return float(get_setting("tax_rate", "0.0"))


# -------------------------------------------------------------------- auth --
def authenticate(pin):
    db = get_db()
    return db.execute(
        "SELECT * FROM users WHERE pin = ? AND active = 1", (pin,)
    ).fetchone()


def list_users(active_only=False):
    db = get_db()
    q = "SELECT * FROM users"
    if active_only:
        q += " WHERE active = 1"
    q += " ORDER BY name"
    return db.execute(q).fetchall()


def create_user(name, pin, role):
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (name, pin, role, active) VALUES (?, ?, ?, 1)",
        (name, pin, role),
    )
    db.commit()
    return cur.lastrowid


def update_user(user_id, name, pin, role, active):
    db = get_db()
    db.execute(
        "UPDATE users SET name=?, pin=?, role=?, active=? WHERE id=?",
        (name, pin, role, int(active), user_id),
    )
    db.commit()


def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()


# -------------------------------------------------------------- categories --
def list_categories():
    db = get_db()
    return db.execute("SELECT * FROM categories ORDER BY sort_order, name").fetchall()


def create_category(name, sort_order=0):
    db = get_db()
    cur = db.execute(
        "INSERT INTO categories (name, sort_order) VALUES (?, ?)", (name, sort_order)
    )
    db.commit()
    return cur.lastrowid


def update_category(cat_id, name, sort_order):
    db = get_db()
    db.execute(
        "UPDATE categories SET name=?, sort_order=? WHERE id=?",
        (name, sort_order, cat_id),
    )
    db.commit()


def delete_category(cat_id):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    db.commit()


# -------------------------------------------------------------- menu items --
def list_menu_items(category_id=None, active_only=True):
    db = get_db()
    q = "SELECT * FROM menu_items WHERE 1=1"
    params = []
    if category_id is not None:
        q += " AND category_id = ?"
        params.append(category_id)
    if active_only:
        q += " AND active = 1"
    q += " ORDER BY sort_order, name"
    return db.execute(q, params).fetchall()


def get_menu_item(item_id):
    db = get_db()
    return db.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()


def create_menu_item(category_id, name, price, active=1, sort_order=0):
    db = get_db()
    cur = db.execute(
        "INSERT INTO menu_items (category_id, name, price, active, sort_order) "
        "VALUES (?, ?, ?, ?, ?)",
        (category_id, name, price, int(active), sort_order),
    )
    db.commit()
    return cur.lastrowid


def update_menu_item(item_id, category_id, name, price, active, sort_order):
    db = get_db()
    db.execute(
        "UPDATE menu_items SET category_id=?, name=?, price=?, active=?, sort_order=? "
        "WHERE id=?",
        (category_id, name, price, int(active), sort_order, item_id),
    )
    db.commit()


def delete_menu_item(item_id):
    db = get_db()
    db.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    db.commit()


def set_item_modifiers(item_id, modifier_ids):
    db = get_db()
    db.execute("DELETE FROM item_modifiers WHERE menu_item_id=?", (item_id,))
    db.executemany(
        "INSERT INTO item_modifiers (menu_item_id, modifier_id) VALUES (?, ?)",
        [(item_id, mid) for mid in modifier_ids],
    )
    db.commit()


def get_item_modifiers(item_id):
    db = get_db()
    return db.execute(
        "SELECT m.* FROM modifiers m "
        "JOIN item_modifiers im ON im.modifier_id = m.id "
        "WHERE im.menu_item_id = ? ORDER BY m.name",
        (item_id,),
    ).fetchall()


# ---------------------------------------------------------------- modifiers --
def list_modifiers():
    db = get_db()
    return db.execute("SELECT * FROM modifiers ORDER BY name").fetchall()


def create_modifier(name, price_delta):
    db = get_db()
    cur = db.execute(
        "INSERT INTO modifiers (name, price_delta) VALUES (?, ?)", (name, price_delta)
    )
    db.commit()
    return cur.lastrowid


def update_modifier(mod_id, name, price_delta):
    db = get_db()
    db.execute(
        "UPDATE modifiers SET name=?, price_delta=? WHERE id=?",
        (name, price_delta, mod_id),
    )
    db.commit()


def delete_modifier(mod_id):
    db = get_db()
    db.execute("DELETE FROM modifiers WHERE id=?", (mod_id,))
    db.commit()


# -------------------------------------------------------------------- cart --
def create_order(cashier_id, order_type="Dine-In"):
    db = get_db()
    cur = db.execute(
        "INSERT INTO orders (order_type, status, cashier_id) VALUES (?, 'draft', ?)",
        (order_type, cashier_id),
    )
    db.commit()
    return cur.lastrowid


def get_order(order_id):
    db = get_db()
    return db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()


def get_order_items(order_id):
    db = get_db()
    items = db.execute(
        "SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)
    ).fetchall()
    result = []
    for item in items:
        mods = db.execute(
            "SELECT * FROM order_item_modifiers WHERE order_item_id=?", (item["id"],)
        ).fetchall()
        result.append({"item": item, "modifiers": mods})
    return result


def set_order_type(order_id, order_type):
    db = get_db()
    db.execute("UPDATE orders SET order_type=? WHERE id=?", (order_type, order_id))
    db.commit()


def add_item_to_order(order_id, menu_item_id, quantity, modifiers, notes=""):
    """modifiers: list of (name, price_delta) tuples."""
    db = get_db()
    item = get_menu_item(menu_item_id)
    cur = db.execute(
        "INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (order_id, menu_item_id, item["name"], item["price"], quantity, notes),
    )
    order_item_id = cur.lastrowid
    db.executemany(
        "INSERT INTO order_item_modifiers (order_item_id, modifier_name, price_delta) "
        "VALUES (?, ?, ?)",
        [(order_item_id, name, delta) for name, delta in modifiers],
    )
    db.commit()
    recalculate_order(order_id)


def update_order_item_quantity(order_item_id, quantity):
    db = get_db()
    row = db.execute(
        "SELECT order_id FROM order_items WHERE id=?", (order_item_id,)
    ).fetchone()
    if quantity <= 0:
        db.execute("DELETE FROM order_items WHERE id=?", (order_item_id,))
    else:
        db.execute(
            "UPDATE order_items SET quantity=? WHERE id=?", (quantity, order_item_id)
        )
    db.commit()
    if row:
        recalculate_order(row["order_id"])


def remove_order_item(order_item_id):
    db = get_db()
    row = db.execute(
        "SELECT order_id FROM order_items WHERE id=?", (order_item_id,)
    ).fetchone()
    db.execute("DELETE FROM order_items WHERE id=?", (order_item_id,))
    db.commit()
    if row:
        recalculate_order(row["order_id"])


def line_total(order_item_row, modifier_rows):
    mods_total = sum(m["price_delta"] for m in modifier_rows)
    return (order_item_row["unit_price"] + mods_total) * order_item_row["quantity"]


def recalculate_order(order_id):
    db = get_db()
    order = get_order(order_id)
    items = get_order_items(order_id)

    subtotal = sum(line_total(i["item"], i["modifiers"]) for i in items)

    discount_amount = 0.0
    if order["discount_type"] == "percent" and order["discount_value"]:
        discount_amount = subtotal * (order["discount_value"] / 100.0)
    elif order["discount_type"] == "amount" and order["discount_value"]:
        discount_amount = min(order["discount_value"], subtotal)

    taxable = max(subtotal - discount_amount, 0.0)
    tax = taxable * get_tax_rate()
    total = taxable + tax

    db.execute(
        "UPDATE orders SET subtotal=?, discount_amount=?, tax=?, total=? WHERE id=?",
        (round(subtotal, 2), round(discount_amount, 2), round(tax, 2), round(total, 2), order_id),
    )
    db.commit()
    return get_order(order_id)


def apply_discount(order_id, discount_type, value):
    db = get_db()
    db.execute(
        "UPDATE orders SET discount_type=?, discount_value=? WHERE id=?",
        (discount_type, value, order_id),
    )
    db.commit()
    recalculate_order(order_id)


def hold_order(order_id):
    update_order_status(order_id, "held")


def recall_order(order_id):
    update_order_status(order_id, "draft")


def get_held_orders():
    db = get_db()
    return db.execute(
        "SELECT * FROM orders WHERE status='held' ORDER BY created_at"
    ).fetchall()


def cancel_order(order_id):
    update_order_status(order_id, "cancelled")


def complete_payment(order_id, payment_method, tendered):
    db = get_db()
    order = recalculate_order(order_id)
    change_due = 0.0
    if payment_method == "Cash":
        change_due = round(max(tendered - order["total"], 0.0), 2)
    db.execute(
        "UPDATE orders SET status='new', payment_method=?, tendered=?, change_due=? "
        "WHERE id=?",
        (payment_method, tendered, change_due, order_id),
    )
    db.commit()
    return get_order(order_id)


def update_order_status(order_id, status):
    db = get_db()
    if status == "completed":
        db.execute(
            "UPDATE orders SET status=?, completed_at=datetime('now','localtime') WHERE id=?",
            (status, order_id),
        )
    else:
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    db.commit()


def get_active_kds_orders():
    db = get_db()
    q = "SELECT * FROM orders WHERE status IN ({}) ORDER BY created_at".format(
        ",".join("?" * len(ACTIVE_KDS_STATUSES))
    )
    return db.execute(q, ACTIVE_KDS_STATUSES).fetchall()


def build_receipt_text(order_id):
    order = get_order(order_id)
    items = get_order_items(order_id)
    name = get_setting("restaurant_name", "Fast Food POS")
    currency = get_setting("currency_symbol", "$")

    lines = []
    width = 40
    lines.append(name.center(width))
    lines.append("Order #{}".format(order["id"]).center(width))
    lines.append(("Type: " + order["order_type"]).center(width))
    lines.append(datetime.now().strftime("%Y-%m-%d %I:%M %p").center(width))
    lines.append("-" * width)

    for entry in items:
        item = entry["item"]
        line = "{:<2}x {:<24}{:>8.2f}".format(
            item["quantity"], item["item_name"][:24], item["unit_price"] * item["quantity"]
        )
        lines.append(line)
        for mod in entry["modifiers"]:
            mod_line = "    + {}".format(mod["modifier_name"])
            if mod["price_delta"]:
                mod_line += " ({:+.2f})".format(mod["price_delta"] * item["quantity"])
            lines.append(mod_line)
        if item["notes"]:
            lines.append("    note: {}".format(item["notes"]))

    lines.append("-" * width)
    lines.append("{:<30}{:>10}".format("Subtotal", "{}{:.2f}".format(currency, order["subtotal"])))
    if order["discount_amount"]:
        lines.append("{:<30}{:>10}".format("Discount", "-{}{:.2f}".format(currency, order["discount_amount"])))
    lines.append("{:<30}{:>10}".format("Tax", "{}{:.2f}".format(currency, order["tax"])))
    lines.append("{:<30}{:>10}".format("TOTAL", "{}{:.2f}".format(currency, order["total"])))
    lines.append("-" * width)
    if order["payment_method"]:
        lines.append("{:<30}{:>10}".format("Paid via", order["payment_method"]))
        if order["payment_method"] == "Cash":
            lines.append("{:<30}{:>10}".format("Tendered", "{}{:.2f}".format(currency, order["tendered"])))
            lines.append("{:<30}{:>10}".format("Change", "{}{:.2f}".format(currency, order["change_due"])))
    lines.append("")
    lines.append("Thank you for your order!".center(width))

    return "\n".join(lines)


# ----------------------------------------------------------------- reports --
def get_daily_summary(date_str):
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS order_count, COALESCE(SUM(total), 0) AS total_sales "
        "FROM orders WHERE status='completed' AND date(completed_at) = ?",
        (date_str,),
    ).fetchone()
    order_count = row["order_count"]
    total_sales = row["total_sales"]
    avg_ticket = (total_sales / order_count) if order_count else 0.0
    return {"order_count": order_count, "total_sales": total_sales, "avg_ticket": avg_ticket}


def get_range_summary(start_date, end_date):
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS order_count, COALESCE(SUM(total), 0) AS total_sales "
        "FROM orders WHERE status='completed' AND date(completed_at) BETWEEN ? AND ?",
        (start_date, end_date),
    ).fetchone()
    order_count = row["order_count"]
    total_sales = row["total_sales"]
    avg_ticket = (total_sales / order_count) if order_count else 0.0
    return {"order_count": order_count, "total_sales": total_sales, "avg_ticket": avg_ticket}


def get_sales_by_day(start_date, end_date):
    db = get_db()
    rows = db.execute(
        "SELECT date(completed_at) AS day, COALESCE(SUM(total), 0) AS total "
        "FROM orders WHERE status='completed' AND date(completed_at) BETWEEN ? AND ? "
        "GROUP BY date(completed_at) ORDER BY day",
        (start_date, end_date),
    ).fetchall()
    return [(r["day"], r["total"]) for r in rows]


def get_top_items(start_date, end_date, limit=10):
    db = get_db()
    rows = db.execute(
        "SELECT oi.item_name AS name, SUM(oi.quantity) AS qty, "
        "SUM(oi.unit_price * oi.quantity) AS revenue "
        "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
        "WHERE o.status='completed' AND date(o.completed_at) BETWEEN ? AND ? "
        "GROUP BY oi.item_name ORDER BY qty DESC LIMIT ?",
        (start_date, end_date, limit),
    ).fetchall()
    return rows


def get_order_history(start_date, end_date):
    db = get_db()
    return db.execute(
        "SELECT * FROM orders WHERE status IN ('completed','cancelled') "
        "AND date(created_at) BETWEEN ? AND ? ORDER BY created_at DESC",
        (start_date, end_date),
    ).fetchall()
