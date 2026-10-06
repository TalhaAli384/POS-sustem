# Fast Food POS

A full point-of-sale system for a fast food restaurant, built with Python, PySide6 (Qt), and SQLite.

## Modules

- **Cashier order screen** — category menu grid, modifiers (e.g. extra cheese, no onions), quantity, notes, discounts, tax calculation, held/parked orders, cash & card payment with change calculation, and a printable receipt.
- **Kitchen Display System (KDS)** — live board of orders in New → Preparing → Ready columns, auto-refreshing, with one-tap status advancement.
- **Admin panel** (admin/manager only) — manage menu items, categories, modifiers, staff accounts/PINs, tax rate, and restaurant settings.
- **Reports** (admin/manager only) — date-range sales summary, daily sales bar chart, and top-selling items.

## Running it

```bash
cd fastfood-pos
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python main.py
```

The SQLite database (`pos.db`) and seed data (sample menu, categories, modifiers, staff) are created automatically on first run.

## Default staff logins (PIN-based)

| Name           | Role     | PIN  |
|----------------|----------|------|
| Owner Admin    | admin    | 1234 |
| Shift Manager  | manager  | 2580 |
| John           | cashier  | 1111 |
| Amy            | cashier  | 2222 |

Cashiers only see the Order and Kitchen Display screens. Admin/Manager also see Admin and Reports.

## Project layout

```
main.py              entry point
database.py          SQLite schema + seed data
models.py            all business logic / data access
ui/
  login_window.py     PIN login dialog
  main_window.py       sidebar navigation shell
  pos_screen.py          cashier order screen + payment/receipt dialogs
  kds_screen.py           kitchen display board
  admin_screen.py          menu/staff/settings management
  reports_screen.py        sales reports + chart
  widgets.py                shared widgets (keypad, menu buttons, bar chart)
receipts/            (reserved for exported receipts)
```
