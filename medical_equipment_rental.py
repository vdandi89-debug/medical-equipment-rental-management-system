"""
MEDICAL EQUIPMENT RENTAL AND RETURN MANAGEMENT SYSTEM
Single-file Flask + MySQL project.

"""

import os
from datetime import date, datetime
from flask import Flask, request, redirect, url_for, flash, render_template_string
import mysql.connector
from mysql.connector import Error

# -------------------- MYSQL CONFIGURATION --------------------

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "vedant123"
DATABASE_NAME = "medical_rental_db"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-local-development-key")


# -------------------- DATABASE CONNECTION --------------------

def server_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DATABASE_NAME
    )


def setup_database():
    conn = server_connection()
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
    cur.close()
    conn.close()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INT AUTO_INCREMENT PRIMARY KEY,
            equipment_name VARCHAR(120) NOT NULL,
            category VARCHAR(80) NOT NULL,
            total_quantity INT NOT NULL,
            available_quantity INT NOT NULL,
            daily_rate DECIMAL(10,2) NOT NULL,
            condition_status VARCHAR(30) NOT NULL DEFAULT 'Good'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            equipment_id INT NOT NULL,
            quantity INT NOT NULL,
            rental_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status VARCHAR(25) NOT NULL DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id)
        )
    """)

    cur.execute("SELECT COUNT(*) FROM equipment")
    if cur.fetchone()[0] == 0:
        starter_equipment = [
            ("Wheelchair", "Mobility", 10, 10, 150.00, "Good"),
            ("Hospital Bed", "Patient Care", 5, 5, 500.00, "Good"),
            ("Oxygen Concentrator", "Respiratory", 6, 6, 650.00, "Good"),
            ("Nebulizer", "Respiratory", 12, 12, 100.00, "Good"),
            ("Patient Monitor", "Monitoring", 4, 4, 700.00, "Good"),
            ("Suction Machine", "Patient Care", 5, 5, 350.00, "Good"),
            ("Walking Frame", "Mobility", 8, 8, 90.00, "Good"),
            ("Infusion Pump", "Treatment", 5, 5, 400.00, "Good"),
            ("Crutches", "Mobility", 15, 15, 60.00, "Good"),
            ("Pulse Oximeter", "Monitoring", 15, 15, 50.00, "Good"),
            ("CPAP Machine", "Respiratory", 4, 4, 550.00, "Good"),
            ("Commode Chair", "Patient Care", 7, 7, 120.00, "Good")
        ]
        cur.executemany("""
            INSERT INTO equipment
            (equipment_name, category, total_quantity, available_quantity, daily_rate, condition_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, starter_equipment)

    conn.commit()
    cur.close()
    conn.close()


# -------------------- SHARED DESIGN --------------------

BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MediRent | {{ page_title }}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box}
body{margin:0;background:#081326;color:#edf3ff;font-family:Inter,Arial,sans-serif;font-size:14px}
.shell{display:flex;min-height:100vh}
.sidebar{width:235px;min-width:235px;background:#0c192d;border-right:1px solid #203451;padding:25px 14px;display:flex;flex-direction:column}
.brand{display:flex;gap:12px;align-items:center;padding:0 8px 35px}
.brand-icon{font-size:30px}.brand b{font-size:19px}
.brand small,.admin small{display:block;color:#91a5c6;font-size:10px;margin-top:5px}
nav{display:grid;gap:9px}
nav a{color:#c5d3eb;text-decoration:none;padding:13px;border-radius:9px;font-weight:600}
nav a:hover,nav a.active{background:#234bc0;color:white}
.side-note{margin-top:auto;text-align:center;border:1px solid #203451;border-radius:12px;padding:20px 12px;line-height:1.6}
.side-note div{font-size:28px}.side-note p{font-size:12px;color:#91a5c6}
main{width:calc(100% - 235px);max-width:1600px;padding:25px 28px;margin:auto}
header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #203451;padding-bottom:18px}
header small{display:block;color:#91a5c6;letter-spacing:2px}
header h1{font-size:23px;margin:5px 0}.admin{text-align:right}
.welcome{display:flex;justify-content:space-between;align-items:center;padding:22px 0}
.welcome h2{margin:0 0 7px;font-size:21px}.welcome p,.muted{color:#91a5c6}.welcome p{margin:0}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
.stat{border-radius:12px;padding:20px;min-height:115px;display:flex;align-items:center;gap:15px}
.stat-icon{font-size:26px;background:#ffffff25;border-radius:50%;width:50px;height:50px;display:grid;place-items:center}
.stat p{margin:0 0 8px}.stat strong{font-size:27px}.stat small{display:block;margin-top:7px}
.purple{background:linear-gradient(120deg,#713ff0,#542bd2)}
.green{background:linear-gradient(120deg,#0da77f,#087e70)}
.blue{background:linear-gradient(120deg,#2387ed,#1458cb)}
.orange{background:linear-gradient(120deg,#ee922d,#d65c1d)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.panel{background:#101f37;border:1px solid #203451;border-radius:12px;padding:18px;min-width:0;margin-bottom:18px}
.panel h3{font-size:15px;margin:0 0 16px}
.equipment-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.equipment-card{background:#0b1930;border:1px solid #31496b;border-radius:10px;padding:14px}
.equipment-card h4{margin:0 0 7px}.equipment-card p{color:#91a5c6;margin:5px 0;font-size:12px}
.tag{display:inline-block;padding:5px 8px;border-radius:20px;background:#0d654e;font-size:10px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:11px 8px;border-bottom:1px solid #203451;font-size:12px}
th{color:#91a5c6}
input,select{width:100%;padding:10px;border:1px solid #31496b;border-radius:7px;background:#0b1930;color:white;margin-top:6px}
label{display:block;color:#a9bbd7;font-size:12px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
button,.button{display:inline-block;padding:11px 15px;border:0;border-radius:7px;background:#2864f0;color:white;font-weight:700;cursor:pointer;text-decoration:none;text-align:center}
button:hover,.button:hover{filter:brightness(1.12)}
.form-grid button{grid-column:1/-1}
.alert{padding:11px;border-radius:7px;margin:10px 0}
.alert.success{background:#0d654e}.alert.error{background:#7b2b38}
.actions{display:flex;gap:8px;align-items:center}
.actions form{margin:0}
@media(max-width:1100px){.stats{grid-template-columns:repeat(2,1fr)}.equipment-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:700px){.sidebar{width:175px;min-width:175px;padding:15px 8px}.brand{padding-bottom:22px}.brand-icon{font-size:23px}.brand b{font-size:15px}.side-note{display:none}nav a{font-size:11px;padding:11px 8px}main{width:calc(100% - 175px);padding:14px 10px}.stats{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.equipment-grid{grid-template-columns:1fr}.form-grid{grid-template-columns:1fr}table{min-width:650px}.panel{overflow-x:auto}}
</style>
</head>
<body>
<div class="shell">
<aside class="sidebar">
 <div class="brand"><span class="brand-icon">🏥</span><div><b>MediRent</b><small>Medical Equipment Care</small></div></div>
 <nav>
  <a class="{{ 'active' if active_page == 'dashboard' else '' }}" href="{{ url_for('dashboard') }}">▦ &nbsp; Dashboard</a>
  <a class="{{ 'active' if active_page == 'equipment' else '' }}" href="{{ url_for('equipment_page') }}">▣ &nbsp; Equipment</a>
  <a class="{{ 'active' if active_page == 'rentals' else '' }}" href="{{ url_for('rentals_page') }}">↗ &nbsp; Rentals</a>
  <a class="{{ 'active' if active_page == 'returns' else '' }}" href="{{ url_for('returns_page') }}">↩ &nbsp; Returns</a>
 </nav>
 <div class="side-note"><div>＋</div><b>Care Made Easier</b><p>Manage medical equipment, rentals and returns in one place.</p></div>
</aside>
<main>
<header><div><small>MEDICAL EQUIPMENT MANAGEMENT</small><h1>{{ page_title }}</h1></div><div class="admin">● &nbsp; Admin<small>Rental Manager</small></div></header>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category,message in messages %}<p class="alert {{ category }}">{{ message }}</p>{% endfor %}{% endif %}
{% endwith %}
{{ page_content|safe }}
</main>
</div>
</body></html>
"""


# -------------------- DASHBOARD --------------------

@app.route("/")
def dashboard():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS total FROM equipment")
        total_equipment = cur.fetchone()["total"]

        cur.execute("SELECT COALESCE(SUM(available_quantity),0) AS total FROM equipment")
        available_units = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM rentals WHERE status='Active'")
        active_rentals = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM rentals WHERE status='Overdue'")
        overdue_rentals = cur.fetchone()["total"]

        cur.execute("""
            SELECT r.id,r.customer_name,r.phone,e.equipment_name,r.quantity,
                   r.rental_date,r.due_date,r.total_amount,r.status
            FROM rentals r JOIN equipment e ON r.equipment_id=e.id
            WHERE r.status IN ('Active','Overdue')
            ORDER BY r.due_date LIMIT 6
        """)
        recent = cur.fetchall()

        cur.execute("""
            SELECT id,equipment_name,category,total_quantity,available_quantity,daily_rate
            FROM equipment ORDER BY equipment_name LIMIT 6
        """)
        equipment = cur.fetchall()

        cur.close()
        conn.close()

        content = render_template_string("""
        <section class="welcome"><div><h2>Welcome Back, Admin! 👋</h2><p>Here's the latest overview of your medical equipment rentals.</p></div><span>📅 {{ today }}</span></section>
        <section class="stats">
          <article class="stat purple"><span class="stat-icon">▣</span><div><p>Equipment Types</p><strong>{{ total_equipment }}</strong><small>Registered items</small></div></article>
          <article class="stat green"><span class="stat-icon">＋</span><div><p>Available Units</p><strong>{{ available_units }}</strong><small>Ready to rent</small></div></article>
          <article class="stat blue"><span class="stat-icon">↗</span><div><p>Active Rentals</p><strong>{{ active_rentals }}</strong><small>Currently rented</small></div></article>
          <article class="stat orange"><span class="stat-icon">◷</span><div><p>Overdue Rentals</p><strong>{{ overdue_rentals }}</strong><small>Past due date</small></div></article>
        </section>
        <section class="panel"><h3>▣ &nbsp; Equipment Availability</h3>
          <div class="equipment-grid">{% for e in equipment %}
          <article class="equipment-card"><h4>{{ e.equipment_name }}</h4><p>{{ e.category }}</p><p>Available: <b>{{ e.available_quantity }}</b> / {{ e.total_quantity }}</p><p>₹{{ "%.2f"|format(e.daily_rate) }} per day</p><span class="tag">In stock</span></article>
          {% endfor %}</div>
          <p><a class="button" href="{{ url_for('equipment_page') }}">View All Equipment</a></p>
        </section>
        <section class="panel"><h3>↗ &nbsp; Active and Overdue Rentals</h3>
        {% if recent %}<table><thead><tr><th>Customer</th><th>Equipment</th><th>Qty</th><th>Due Date</th><th>Amount</th><th>Status</th></tr></thead><tbody>
        {% for r in recent %}<tr><td>{{ r.customer_name }}<br><span class="muted">{{ r.phone }}</span></td><td>{{ r.equipment_name }}</td><td>{{ r.quantity }}</td><td>{{ r.due_date }}</td><td>₹{{ "%.2f"|format(r.total_amount) }}</td><td>{{ r.status }}</td></tr>{% endfor %}
        </tbody></table>{% else %}<p class="muted">No active rentals at the moment.</p>{% endif %}
        </section>
        <section class="grid">
          <a class="button" href="{{ url_for('rent_equipment') }}">＋ Create New Rental</a>
          <a class="button" href="{{ url_for('returns_page') }}">↩ Manage Equipment Returns</a>
        </section>
        """, total_equipment=total_equipment, available_units=available_units,
             active_rentals=active_rentals, overdue_rentals=overdue_rentals,
             recent=recent, equipment=equipment, today=date.today().strftime("%d %b %Y"))

        return render_template_string(BASE_HTML, page_title="Dashboard",
                                      page_content=content, active_page="dashboard")
    except Error as error:
        return f"<h2>Database connection error</h2><p>Check MySQL settings.</p><pre>{error}</pre>", 500


# -------------------- EQUIPMENT INVENTORY --------------------

@app.route("/equipment")
def equipment_page():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM equipment ORDER BY equipment_name")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        content = render_template_string("""
        <section class="panel"><h3>Medical Equipment Inventory</h3>
        <p class="muted">Check equipment stock, rental rates and availability.</p>
        <table><thead><tr><th>Equipment</th><th>Category</th><th>Total Units</th><th>Available</th><th>Daily Rate</th><th>Condition</th></tr></thead><tbody>
        {% for e in rows %}<tr><td><b>{{ e.equipment_name }}</b></td><td>{{ e.category }}</td><td>{{ e.total_quantity }}</td><td>{{ e.available_quantity }}</td><td>₹{{ "%.2f"|format(e.daily_rate) }}</td><td>{{ e.condition_status }}</td></tr>{% endfor %}
        </tbody></table></section>
        """, rows=rows)
        return render_template_string(BASE_HTML, page_title="Equipment Inventory",
                                      page_content=content, active_page="equipment")
    except Error as error:
        return f"<h2>Database error</h2><pre>{error}</pre>", 500


# -------------------- CREATE RENTAL --------------------

@app.route("/rent", methods=["GET", "POST"])
def rent_equipment():
    if request.method == "POST":
        customer = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        equipment_id = request.form.get("equipment_id", type=int)
        quantity = request.form.get("quantity", type=int)
        rental_date = request.form.get("rental_date")
        due_date = request.form.get("due_date")

        if not all([customer, phone, equipment_id, quantity, rental_date, due_date]):
            flash("Please complete every field.", "error")
            return redirect(url_for("rent_equipment"))

        try:
            start = date.fromisoformat(rental_date)
            end = date.fromisoformat(due_date)
            if quantity < 1 or end < start:
                flash("Enter a valid quantity and due date.", "error")
                return redirect(url_for("rent_equipment"))

            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM equipment WHERE id=%s FOR UPDATE", (equipment_id,))
            item = cur.fetchone()

            if not item or quantity > item["available_quantity"]:
                conn.rollback()
                cur.close()
                conn.close()
                flash("Not enough equipment units are available.", "error")
                return redirect(url_for("rent_equipment"))

            days = (end - start).days + 1
            amount = float(item["daily_rate"]) * quantity * days

            cur.execute("""
                INSERT INTO rentals
                (customer_name,phone,equipment_id,quantity,rental_date,due_date,total_amount,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'Active')
            """, (customer, phone, equipment_id, quantity, rental_date, due_date, amount))

            cur.execute("""
                UPDATE equipment SET available_quantity=available_quantity-%s
                WHERE id=%s
            """, (quantity, equipment_id))

            conn.commit()
            cur.close()
            conn.close()
            flash("Rental created successfully!", "success")
            return redirect(url_for("rentals_page"))

        except (ValueError, Error) as error:
            flash("Could not create rental: " + str(error), "error")
            return redirect(url_for("rent_equipment"))

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,equipment_name,available_quantity,daily_rate FROM equipment WHERE available_quantity>0 ORDER BY equipment_name")
        items = cur.fetchall()
        cur.close()
        conn.close()

        content = render_template_string("""
        <section class="panel"><h3>＋ Create Equipment Rental</h3>
        <p class="muted">Enter customer details and rental period. Amount is calculated automatically.</p>
        <form class="form-grid" method="POST">
          <label>Customer Name<input name="customer_name" placeholder="e.g. Rahul Sharma" required></label>
          <label>Phone Number<input name="phone" type="tel" placeholder="Mobile number" required></label>
          <label>Medical Equipment<select name="equipment_id" required><option value="">Choose equipment</option>{% for e in items %}<option value="{{ e.id }}">{{ e.equipment_name }} — {{ e.available_quantity }} available (₹{{ "%.2f"|format(e.daily_rate) }}/day)</option>{% endfor %}</select></label>
          <label>Quantity<input name="quantity" type="number" min="1" value="1" required></label>
          <label>Rental Date<input name="rental_date" type="date" min="{{ today }}" value="{{ today }}" required></label>
          <label>Expected Return Date<input name="due_date" type="date" min="{{ today }}" required></label>
          <button type="submit">Create Rental</button>
        </form></section>
        """, items=items, today=date.today().isoformat())
        return render_template_string(BASE_HTML, page_title="New Rental",
                                      page_content=content, active_page="rentals")
    except Error as error:
        return f"<h2>Database error</h2><pre>{error}</pre>", 500


# -------------------- RENTAL RECORDS --------------------

@app.route("/rentals")
def rentals_page():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT r.*,e.equipment_name FROM rentals r
            JOIN equipment e ON r.equipment_id=e.id
            ORDER BY r.id DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        content = render_template_string("""
        <section class="panel"><h3>All Rental Records</h3>
        <p class="muted">Track rented equipment, customers, due dates and rental status.</p>
        <table><thead><tr><th>ID</th><th>Customer</th><th>Equipment</th><th>Qty</th><th>Rental Date</th><th>Due Date</th><th>Amount</th><th>Status</th></tr></thead><tbody>
        {% for r in rows %}<tr><td>#{{ r.id }}</td><td>{{ r.customer_name }}<br><span class="muted">{{ r.phone }}</span></td><td>{{ r.equipment_name }}</td><td>{{ r.quantity }}</td><td>{{ r.rental_date }}</td><td>{{ r.due_date }}</td><td>₹{{ "%.2f"|format(r.total_amount) }}</td><td>{{ r.status }}</td></tr>{% endfor %}
        </tbody></table>{% if not rows %}<p class="muted">No rentals created yet.</p>{% endif %}
        <p><a class="button" href="{{ url_for('rent_equipment') }}">＋ New Rental</a></p>
        </section>
        """, rows=rows)
        return render_template_string(BASE_HTML, page_title="Rental Records",
                                      page_content=content, active_page="rentals")
    except Error as error:
        return f"<h2>Database error</h2><pre>{error}</pre>", 500


# -------------------- RETURN MANAGEMENT --------------------

@app.route("/returns")
def returns_page():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # Mark active rentals as overdue when their due date has passed.
        cur.execute("""
            UPDATE rentals SET status='Overdue'
            WHERE status='Active' AND due_date < CURDATE()
        """)
        conn.commit()

        cur.execute("""
            SELECT r.id,r.customer_name,r.phone,e.equipment_name,r.quantity,
                   r.rental_date,r.due_date,r.total_amount,r.status
            FROM rentals r JOIN equipment e ON r.equipment_id=e.id
            WHERE r.status IN ('Active','Overdue')
            ORDER BY r.due_date
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        content = render_template_string("""
        <section class="panel"><h3>↩ Equipment Return Management</h3>
        <p class="muted">When equipment is returned, select the Return button. Its quantity will be added back to available stock.</p>
        {% if rows %}<table><thead><tr><th>Rental ID</th><th>Customer</th><th>Equipment</th><th>Qty</th><th>Due Date</th><th>Status</th><th>Action</th></tr></thead><tbody>
        {% for r in rows %}<tr><td>#{{ r.id }}</td><td>{{ r.customer_name }}<br><span class="muted">{{ r.phone }}</span></td><td>{{ r.equipment_name }}</td><td>{{ r.quantity }}</td><td>{{ r.due_date }}</td><td>{{ r.status }}</td><td>
        <form method="POST" action="{{ url_for('return_rental', rental_id=r.id) }}" onsubmit="return confirm('Confirm that this equipment has been returned?')"><button type="submit">Mark Returned</button></form>
        </td></tr>{% endfor %}
        </tbody></table>{% else %}<p class="muted">There are no pending equipment returns.</p>{% endif %}
        </section>
        """, rows=rows)
        return render_template_string(BASE_HTML, page_title="Returns",
                                      page_content=content, active_page="returns")
    except Error as error:
        return f"<h2>Database error</h2><pre>{error}</pre>", 500


@app.route("/return/<int:rental_id>", methods=["POST"])
def return_rental(rental_id):
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM rentals WHERE id=%s FOR UPDATE", (rental_id,))
        rental = cur.fetchone()

        if not rental or rental["status"] not in ("Active", "Overdue"):
            conn.rollback()
            cur.close()
            conn.close()
            flash("This rental cannot be returned again.", "error")
            return redirect(url_for("returns_page"))

        cur.execute("""
            UPDATE rentals SET status='Returned', return_date=CURDATE()
            WHERE id=%s
        """, (rental_id,))

        cur.execute("""
            UPDATE equipment SET available_quantity=available_quantity+%s
            WHERE id=%s
        """, (rental["quantity"], rental["equipment_id"]))

        conn.commit()
        cur.close()
        conn.close()
        flash("Equipment return recorded and stock updated.", "success")
    except Error as error:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        flash("Return could not be recorded: " + str(error), "error")

    return redirect(url_for("returns_page"))


# -------------------- START APPLICATION --------------------

if __name__ == "__main__":
    try:
        setup_database()
        print("MySQL database and tables are ready.")
        print("Starting MediRent dashboard at http://127.0.0.1:5000")
        app.run(debug=True)
    except Error as error:
        print("Could not connect to MySQL.")
        print("Check MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD and MySQL Server.")
        print("Details:", error)
