from flask import Flask, request, redirect, session
import sqlite3
from html import escape
from functools import wraps
from datetime import datetime

app = Flask(__name__)

DB = "complaints.db"

app.secret_key = "complaint-management-secret-key-2026"


# =========================================================
# DATABASE
# =========================================================

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():

    conn = db()

    # -------------------------
    # USERS
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User'
        )
    """)

    # -------------------------
    # COMPLAINTS
    # -------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_no TEXT,
            date TEXT,
            time TEXT,
            complainant TEXT,
            location TEXT,
            complaint_type TEXT,
            details TEXT,
            assigned TEXT,
            status TEXT,
            remarks TEXT
        )
    """)

    # -------------------------
    # DATABASE MIGRATION
    # -------------------------

    columns = conn.execute(
        "PRAGMA table_info(complaints)"
    ).fetchall()

    existing_columns = [
        row["name"] for row in columns
    ]

    required_columns = {
        "complaint_no": "TEXT",
        "date": "TEXT",
        "time": "TEXT",
        "complainant": "TEXT",
        "location": "TEXT",
        "complaint_type": "TEXT",
        "details": "TEXT",
        "assigned": "TEXT",
        "status": "TEXT",
        "remarks": "TEXT"
    }

    for column, data_type in required_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE complaints ADD COLUMN {column} {data_type}"
            )

    # -------------------------
    # DEFAULT ADMIN
    # -------------------------

    admin = conn.execute(
        "SELECT id FROM users WHERE username=?",
        ("admin",)
    ).fetchone()

    if admin is None:

        conn.execute(
            """
            INSERT INTO users
            (username, password, role)
            VALUES (?, ?, ?)
            """,
            ("admin", "admin123", "Admin")
        )

    conn.commit()
    conn.close()


setup_database()


# =========================================================
# LOGIN
# =========================================================

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/login")

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/login")

        if session.get("role") != "Admin":

            return page(
                "Access Denied",
                """
                <div class="box center">
                    <h2>Access Denied</h2>
                    <p>Only Admin can perform this action.</p>
                </div>

                <a class="button" href="/">
                    Back to Dashboard
                </a>
                """
            )

        return func(*args, **kwargs)

    return wrapper


# =========================================================
# AUTOMATIC COMPLAINT NUMBER
# =========================================================

def generate_complaint_number(date_value):

    try:
        dt = datetime.strptime(
            date_value,
            "%Y-%m-%d"
        )

    except ValueError:

        dt = datetime.now()

    year = dt.strftime("%Y")
    month = dt.strftime("%m")

    prefix = f"CMP-{year}-{month}-"

    conn = db()

    row = conn.execute(
        """
        SELECT complaint_no
        FROM complaints
        WHERE complaint_no LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (prefix + "%",)
    ).fetchone()

    conn.close()

    if row is None:

        number = 1

    else:

        try:

            old_number = str(
                row["complaint_no"]
            )

            last_part = old_number.split("-")[-1]

            number = int(last_part) + 1

        except:

            number = 1

    return prefix + str(number).zfill(3)


# =========================================================
# STYLE
# =========================================================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f1f3f6;
    margin: 0;
    padding: 15px;
    color: #222;
}

.container {
    max-width: 1250px;
    margin: auto;
}

.header {
    background: #20252b;
    color: white;
    padding: 22px;
    text-align: center;
    border-radius: 10px;
}

.header h1 {
    margin: 0;
    font-size: 27px;
}

.header p {
    margin-bottom: 0;
}

.topbar {
    background: white;
    padding: 12px;
    margin-top: 15px;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.user-info {
    font-weight: bold;
}

.box {
    background: white;
    padding: 18px;
    margin-top: 15px;
    border-radius: 8px;
}

.center {
    text-align: center;
}

.cardbox {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 15px;
}

.card {
    background: white;
    padding: 18px;
    text-align: center;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08);
}

.num {
    font-size: 32px;
    font-weight: bold;
    margin-top: 8px;
}

.button {
    display: block;
    background: #20252b;
    color: white;
    text-decoration: none;
    padding: 13px;
    margin-top: 10px;
    text-align: center;
    border-radius: 6px;
}

.button.blue {
    background: #2878b5;
}

.button.green {
    background: #287a45;
}

.button.gray {
    background: #777;
}

.button.red {
    background: #a00000;
}

.button.small {
    display: inline-block;
    padding: 8px 12px;
    margin-top: 0;
}

input,
select,
textarea {
    width: 100%;
    padding: 11px;
    margin: 5px 0 12px 0;
    border: 1px solid #bbb;
    border-radius: 5px;
    font-size: 15px;
}

textarea {
    min-height: 90px;
    resize: vertical;
}

label {
    font-weight: bold;
    display: block;
    margin-top: 8px;
}

button {
    width: 100%;
    padding: 13px;
    background: #20252b;
    color: white;
    border: 0;
    border-radius: 6px;
    font-size: 15px;
    cursor: pointer;
}

.tablebox {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    border: 1px solid #ccc;
    padding: 8px;
    white-space: nowrap;
}

th {
    background: #20252b;
    color: white;
}

.action {
    color: white;
    padding: 6px 9px;
    text-decoration: none;
    border-radius: 4px;
    display: inline-block;
    margin: 2px;
}

.view {
    background: #2878b5;
}

.edit {
    background: #555;
}

.delete {
    background: #a00000;
}

.filterbox {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.detail {
    background: white;
    padding: 20px;
    margin-top: 15px;
    border-radius: 8px;
}

.detail p {
    border-bottom: 1px solid #ddd;
    padding-bottom: 10px;
}

.login-box {
    max-width: 450px;
    margin: 50px auto;
    background: white;
    padding: 25px;
    border-radius: 10px;
}

.login-title {
    text-align: center;
    margin-bottom: 20px;
}

.error {
    background: #ffe0e0;
    color: #900;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 15px;
}

.success {
    background: #e0ffe8;
    color: #176b2d;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 15px;
}

.report-header {
    text-align: center;
    margin-bottom: 20px;
}

.report-info {
    background: #f5f5f5;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 15px;
}

.summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 15px;
}

.summary-box {
    border: 1px solid #ccc;
    padding: 12px;
    text-align: center;
    background: white;
}

.summary-number {
    font-size: 25px;
    font-weight: bold;
}

.quick-buttons {
    margin-top: 15px;
}

.notice {
    background: #fff8df;
    border: 1px solid #e4d28b;
    padding: 12px;
    border-radius: 6px;
    margin-top: 15px;
}

@media (max-width: 700px) {

    .cardbox {
        grid-template-columns: repeat(2, 1fr);
    }

    .summary {
        grid-template-columns: repeat(2, 1fr);
    }

    .filterbox {
        grid-template-columns: 1fr;
    }

    .header h1 {
        font-size: 22px;
    }

    body {
        padding: 8px;
    }

}

@media print {

    body {
        background: white;
        padding: 0;
    }

    .no-print {
        display: none !important;
    }

    .container {
        max-width: none;
    }

    table {
        font-size: 10px;
    }

    th,
    td {
        white-space: normal;
    }

}

</style>
"""


# =========================================================
# PAGE TEMPLATE
# =========================================================

def page(title, body):

    user_bar = ""

    if "user_id" in session:

        user_bar = (
            "<div class='topbar no-print'>"

            "<div class='user-info'>"
            "Logged in: " +
            escape(str(session.get("username", ""))) +
            " (" +
            escape(str(session.get("role", ""))) +
            ")"
            "</div>"

            "<div>"
            "<a class='button red small' href='/logout'>"
            "Logout"
            "</a>"
            "</div>"

            "</div>"
        )

    return (
        "<!DOCTYPE html>"
        "<html>"
        "<head>"
        "<title>" +
        escape(title) +
        "</title>"
        "<meta name='viewport' "
        "content='width=device-width, initial-scale=1'>"
        +
        STYLE +
        "</head>"
        "<body>"
        "<div class='container'>"
        +
        user_bar +
        body +
        "</div>"
        "</body>"
        "</html>"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conn = db()

        user = conn.execute(
            """
            SELECT id, username, password, role
            FROM users
            WHERE username=? AND password=?
            """,
            (username, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect("/")

        error = "Invalid username or password."

    error_html = ""

    if error:

        error_html = (
            "<div class='error'>" +
            escape(error) +
            "</div>"
        )

    body = (

        "<div class='login-box'>"

        "<div class='login-title'>"
        "<h1>Complaint Management System</h1>"
        "<h2>Login</h2>"
        "</div>"

        +
        error_html
        +

        "<form method='POST'>"

        "<label>Username</label>"
        "<input "
        "name='username' "
        "placeholder='Enter username' "
        "required>"

        "<label>Password</label>"
        "<input "
        "type='password' "
        "name='password' "
        "placeholder='Enter password' "
        "required>"

        "<button type='submit'>"
        "Login"
        "</button>"

        "</form>"

        "<div class='notice'>"
        "<b>Default Admin:</b><br>"
        "Username: admin<br>"
        "Password: admin123"
        "</div>"

        "</div>"
    )

    return page(
        "Login",
        body
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def home():

    conn = db()

    total = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM complaints "
        "WHERE status='Pending'"
    ).fetchone()[0]

    progress = conn.execute(
        "SELECT COUNT(*) FROM complaints "
        "WHERE status='In Progress'"
    ).fetchone()[0]

    completed = conn.execute(
        "SELECT COUNT(*) FROM complaints "
        "WHERE status='Completed'"
    ).fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")

    today_count = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE date=?",
        (today,)
    ).fetchone()[0]

    recent = conn.execute(
        """
        SELECT *
        FROM complaints
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    conn.close()

    rows = ""

    for r in recent:

        rows += (
            "<tr>"

            "<td>" +
            escape(str(r["complaint_no"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["date"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["location"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["complaint_type"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["status"] or "")) +
            "</td>"

            "</tr>"
        )

    if not rows:

        rows = (
            "<tr>"
            "<td colspan='5' style='text-align:center'>"
            "No complaints yet."
            "</td>"
            "</tr>"
        )

    body = (

        "<div class='header'>"
        "<h1>Complaint Management System</h1>"
        "<p>Dashboard</p>"
        "</div>"

        "<div class='cardbox'>"

        "<div class='card'>"
        "Total Complaints"
        "<div class='num'>" +
        str(total) +
        "</div>"
        "</div>"

        "<div class='card'>"
        "Today"
        "<div class='num'>" +
        str(today_count) +
        "</div>"
        "</div>"

        "<div class='card'>"
        "Pending"
        "<div class='num'>" +
        str(pending) +
        "</div>"
        "</div>"

        "<div class='card'>"
        "Completed"
        "<div class='num'>" +
        str(completed) +
        "</div>"
        "</div>"

        "</div>"

        "<div class='box'>"
        "<h2>Recent Complaints</h2>"

        "<div class='tablebox'>"
        "<table>"

        "<tr>"
        "<th>Complaint No.</th>"
        "<th>Date</th>"
        "<th>Location</th>"
        "<th>Type</th>"
        "<th>Status</th>"
        "</tr>"

        +
        rows
        +

        "</table>"
        "</div>"
        "</div>"

        "<div class='quick-buttons'>"

        "<a class='button' href='/add'>"
        "➕ Add New Complaint"
        "</a>"

        "<a class='button blue' href='/complaints'>"
        "📋 View All Complaints"
        "</a>"

        "<a class='button green' href='/reports'>"
        "📊 Reports"
        "</a>"
    )

    if session.get("role") == "Admin":

        body += (
            "<a class='button' href='/users'>"
            "👥 User Management"
            "</a>"
        )

    body += "</div>"

    return page(
        "Dashboard",
        body
    )


# =========================================================
# ADD COMPLAINT
# =========================================================

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():

    if request.method == "POST":

        date_value = request.form.get(
            "date",
            ""
        ).strip()

        if not date_value:

            date_value = datetime.now().strftime(
                "%Y-%m-%d"
            )

        complaint_no = generate_complaint_number(
            date_value
        )

        data = (

            complaint_no,

            date_value,

            request.form.get(
                "time",
                ""
            ),

            request.form.get(
                "complainant",
                ""
            ),

            request.form.get(
                "location",
                ""
            ),

            request.form.get(
                "complaint_type",
                ""
            ),

            request.form.get(
                "details",
                ""
            ),

            request.form.get(
                "assigned",
                ""
            ),

            request.form.get(
                "status",
                "Pending"
            ),

            request.form.get(
                "remarks",
                ""
            )
        )

        conn = db()

        conn.execute(
            """
            INSERT INTO complaints
            (
                complaint_no,
                date,
                time,
                complainant,
                location,
                complaint_type,
                details,
                assigned,
                status,
                remarks
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data
        )

        conn.commit()
        conn.close()

        return redirect("/view/" + str(
            conn_id_after_insert()
        ))

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    now_time = datetime.now().strftime(
        "%H:%M"
    )

    preview_no = generate_complaint_number(
        today
    )

    body = (

        "<div class='header'>"
        "<h1>Add New Complaint</h1>"
        "</div>"

        "<div class='box'>"

        "<div class='notice'>"
        "<b>Automatic Complaint No.:</b> " +
        escape(preview_no) +
        "<br>"
        "Complaint number will automatically continue month-wise."
        "</div>"

        "<form method='POST'>"

        "<label>Complaint No.</label>"
        "<input "
        "value='" +
        escape(preview_no) +
        "' "
        "readonly>"

        "<label>Date</label>"
        "<input "
        "type='date' "
        "name='date' "
        "value='" +
        today +
        "' "
        "required>"

        "<label>Time</label>"
        "<input "
        "type='time' "
        "name='time' "
        "value='" +
        now_time +
        "' "
        "required>"

        "<label>Complainant</label>"
        "<input name='complainant'>"

        "<label>Location</label>"
        "<input "
        "name='location' "
        "placeholder='Enter complaint location' "
        "required>"

        "<label>Complaint Type</label>"

        "<select name='complaint_type'>"

        "<option>Plumbing</option>"
        "<option>Carpenter</option>"
        "<option>Masonry</option>"
        "<option>Painter</option>"
        "<option>Sewer</option>"
        "<option>Metal Work</option>"
        "<option>Horticulture</option>"
        "<option>Electrical</option>"
        "<option>Other</option>"

        "</select>"

        "<label>Complaint Details</label>"
        "<textarea "
        "name='details' "
        "placeholder='Enter complaint details' "
        "required></textarea>"

        "<label>Assigned Staff</label>"
        "<input "
        "name='assigned' "
        "placeholder='Enter assigned staff'>"

        "<label>Status</label>"

        "<select name='status'>"
        "<option>Pending</option>"
        "<option>In Progress</option>"
        "<option>Completed</option>"
        "</select>"

        "<label>Remarks</label>"
        "<textarea "
        "name='remarks' "
        "placeholder='Enter remarks'></textarea>"

        "<button type='submit'>"
        "Save Complaint"
        "</button>"

        "</form>"

        "</div>"

        "<a class='button' href='/'>"
        "Back to Dashboard"
        "</a>"
    )

    return page(
        "Add Complaint",
        body
    )


# =========================================================
# GET LAST INSERTED COMPLAINT
# =========================================================

def conn_id_after_insert():

    conn = db()

    row = conn.execute(
        "SELECT id FROM complaints ORDER BY id DESC LIMIT 1"
    ).fetchone()

    conn.close()

    if row:
        return row["id"]

    return 1


# =========================================================
# ALL COMPLAINTS
# =========================================================

@app.route("/complaints")
@login_required
def complaints():

    search = request.args.get(
        "search",
        ""
    ).strip()

    status_filter = request.args.get(
        "status",
        ""
    ).strip()

    type_filter = request.args.get(
        "complaint_type",
        ""
    ).strip()

    date_filter = request.args.get(
        "date",
        ""
    ).strip()

    conn = db()

    conditions = []
    values = []

    if search:

        conditions.append(
            """
            (
                complaint_no LIKE ?
                OR complainant LIKE ?
                OR location LIKE ?
                OR details LIKE ?
                OR assigned LIKE ?
            )
            """
        )

        s = "%" + search + "%"

        values.extend([
            s,
            s,
            s,
            s,
            s
        ])

    if status_filter:

        conditions.append(
            "status = ?"
        )

        values.append(
            status_filter
        )

    if type_filter:

        conditions.append(
            "complaint_type = ?"
        )

        values.append(
            type_filter
        )

    if date_filter:

        conditions.append(
            "date = ?"
        )

        values.append(
            date_filter
        )

    query = "SELECT * FROM complaints"

    if conditions:

        query += (
            " WHERE " +
            " AND ".join(conditions)
        )

    query += " ORDER BY id DESC"

    rows = conn.execute(
        query,
        values
    ).fetchall()

    conn.close()

    table = ""

    for r in rows:

        actions = (

            "<a class='action view' "
            "href='/view/" +
            str(r["id"]) +
            "'>"
            "View"
            "</a>"

            "<a class='action edit' "
            "href='/edit/" +
            str(r["id"]) +
            "'>"
            "Edit"
            "</a>"
        )

        if session.get("role") == "Admin":

            actions += (

                "<a class='action delete' "
                "href='/delete/" +
                str(r["id"]) +
                "' "
                "onclick=\"return confirm('Delete this complaint?')\">"
                "Delete"
                "</a>"
            )

        table += (

            "<tr>"

            "<td>" +
            escape(str(r["complaint_no"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["date"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["time"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["complainant"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["location"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["complaint_type"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["status"] or "")) +
            "</td>"

            "<td>" +
            actions +
            "</td>"

            "</tr>"
        )

    if not table:

        table = (
            "<tr>"
            "<td colspan='8' style='text-align:center'>"
            "No complaints found."
            "</td>"
            "</tr>"
        )

    body = (

        "<div class='header'>"
        "<h1>All Complaints</h1>"
        "</div>"

        "<div class='box no-print'>"

        "<h2>Search & Filter</h2>"

        "<form method='GET'>"

        "<div class='filterbox'>"

        "<div>"

        "<label>Search</label>"

        "<input "
        "name='search' "
        "placeholder='Complaint No, Location, Complainant...' "
        "value='" +
        escape(search) +
        "'>"

        "</div>"

        "<div>"

        "<label>Status</label>"

        "<select name='status'>"

        "<option value=''>All Status</option>"

        "<option value='Pending' " +
        ("selected" if status_filter == "Pending" else "") +
        ">Pending</option>"

        "<option value='In Progress' " +
        ("selected" if status_filter == "In Progress" else "") +
        ">In Progress</option>"

        "<option value='Completed' " +
        ("selected" if status_filter == "Completed" else "") +
        ">Completed</option>"

        "</select>"

        "</div>"

        "<div>"

        "<label>Complaint Type</label>"

        "<select name='complaint_type'>"

        "<option value=''>All Types</option>"
        "<option value='Plumbing'>Plumbing</option>"
        "<option value='Carpenter'>Carpenter</option>"
        "<option value='Masonry'>Masonry</option>"
        "<option value='Painter'>Painter</option>"
        "<option value='Sewer'>Sewer</option>"
        "<option value='Metal Work'>Metal Work</option>"
        "<option value='Horticulture'>Horticulture</option>"
        "<option value='Electrical'>Electrical</option>"
        "<option value='Other'>Other</option>"

        "</select>"

        "</div>"

        "</div>"

        "<label>Date</label>"

        "<input "
        "type='date' "
        "name='date' "
        "value='" +
        escape(date_filter) +
        "'>"

        "<button type='submit'>"
        "Apply Filter"
        "</button>"

        "</form>"

        "<a class='button gray' href='/complaints'>"
        "Clear Filters"
        "</a>"

        "</div>"

        "<div class='box'>"

        "<div class='tablebox'>"

        "<table>"

        "<tr>"
        "<th>Complaint No.</th>"
        "<th>Date</th>"
        "<th>Time</th>"
        "<th>Complainant</th>"
        "<th>Location</th>"
        "<th>Type</th>"
        "<th>Status</th>"
        "<th>Action</th>"
        "</tr>"

        +
        table
        +

        "</table>"

        "</div>"
        "</div>"

        "<a class='button' href='/add'>"
        "Add New Complaint"
        "</a>"

        "<a class='button green' href='/reports'>"
        "Reports"
        "</a>"

        "<a class='button' href='/'>"
        "Back to Dashboard"
        "</a>"
    )

    return page(
        "All Complaints",
        body
    )


# =========================================================
# VIEW COMPLAINT
# =========================================================

@app.route("/view/<int:item_id>")
@login_required
def view_complaint(item_id):

    conn = db()

    row = conn.execute(
        "SELECT * FROM complaints WHERE id=?",
        (item_id,)
    ).fetchone()

    conn.close()

    if row is None:

        return page(
            "Not Found",
            """
            <div class='box center'>
                <h2>Complaint not found.</h2>
            </div>
            """
        )

    body = (

        "<div class='header'>"
        "<h1>Complaint Details</h1>"
        "</div>"

        "<div class='detail'>"

        "<p><b>Complaint No.:</b><br>" +
        escape(str(row["complaint_no"] or "")) +
        "</p>"

        "<p><b>Date:</b><br>" +
        escape(str(row["date"] or "")) +
        "</p>"

        "<p><b>Time:</b><br>" +
        escape(str(row["time"] or "")) +
        "</p>"

        "<p><b>Complainant:</b><br>" +
        escape(str(row["complainant"] or "")) +
        "</p>"

        "<p><b>Location:</b><br>" +
        escape(str(row["location"] or "")) +
        "</p>"

        "<p><b>Complaint Type:</b><br>" +
        escape(str(row["complaint_type"] or "")) +
        "</p>"

        "<p><b>Complaint Details:</b><br>" +
        escape(str(row["details"] or "")) +
        "</p>"

        "<p><b>Assigned Staff:</b><br>" +
        escape(str(row["assigned"] or "")) +
        "</p>"

        "<p><b>Status:</b><br>" +
        escape(str(row["status"] or "")) +
        "</p>"

        "<p><b>Remarks:</b><br>" +
        escape(str(row["remarks"] or "")) +
        "</p>"

        "</div>"

        "<a class='button' href='/edit/" +
        str(row["id"]) +
        "'>"
        "Edit Complaint"
        "</a>"

        "<a class='button blue' "
        "href='/complaints'>"
        "Back to All Complaints"
        "</a>"
    )

    return page(
        "Complaint Details",
        body
    )


# =========================================================
# EDIT COMPLAINT
# =========================================================

@app.route(
    "/edit/<int:item_id>",
    methods=["GET", "POST"]
)
@login_required
def edit(item_id):

    conn = db()

    row = conn.execute(
        "SELECT * FROM complaints WHERE id=?",
        (item_id,)
    ).fetchone()

    if row is None:

        conn.close()

        return page(
            "Not Found",
            """
            <div class='box center'>
                <h2>Complaint not found.</h2>
            </div>
            """
        )

    if request.method == "POST":

        data = (

            request.form.get(
                "complaint_no",
                ""
            ),

            request.form.get(
                "date",
                ""
            ),

            request.form.get(
                "time",
                ""
            ),

            request.form.get(
                "complainant",
                ""
            ),

            request.form.get(
                "location",
                ""
            ),

            request.form.get(
                "complaint_type",
                ""
            ),

            request.form.get(
                "details",
                ""
            ),

            request.form.get(
                "assigned",
                ""
            ),

            request.form.get(
                "status",
                ""
            ),

            request.form.get(
                "remarks",
                ""
            ),

            item_id
        )

        conn.execute(
            """
            UPDATE complaints SET
            complaint_no=?,
            date=?,
            time=?,
            complainant=?,
            location=?,
            complaint_type=?,
            details=?,
            assigned=?,
            status=?,
            remarks=?
            WHERE id=?
            """,
            data
        )

        conn.commit()
        conn.close()

        return redirect("/complaints")

    complaint_type = str(
        row["complaint_type"] or ""
    )

    status = str(
        row["status"] or ""
    )

    types = [
        "Plumbing",
        "Carpenter",
        "Masonry",
        "Painter",
        "Sewer",
        "Metal Work",
        "Horticulture",
        "Electrical",
        "Other"
    ]

    type_options = ""

    for t in types:

        selected = (
            " selected"
            if t == complaint_type
            else ""
        )

        type_options += (
            "<option value='" +
            escape(t) +
            "'" +
            selected +
            ">" +
            escape(t) +
            "</option>"
        )

    status_options = ""

    for s in [
        "Pending",
        "In Progress",
        "Completed"
    ]:

        selected = (
            " selected"
            if s == status
            else ""
        )

        status_options += (
            "<option value='" +
            escape(s) +
            "'" +
            selected +
            ">" +
            escape(s) +
            "</option>"
        )

    body = (

        "<div class='header'>"
        "<h1>Edit Complaint</h1>"
        "</div>"

        "<div class='box'>"

        "<form method='POST'>"

        "<label>Complaint No.</label>"
        "<input name='complaint_no' "
        "value='" +
        escape(str(row["complaint_no"] or "")) +
        "' readonly>"

        "<label>Date</label>"
        "<input type='date' name='date' "
        "value='" +
        escape(str(row["date"] or "")) +
        "' required>"

        "<label>Time</label>"
        "<input type='time' name='time' "
        "value='" +
        escape(str(row["time"] or "")) +
        "' required>"

        "<label>Complainant</label>"
        "<input name='complainant' "
        "value='" +
        escape(str(row["complainant"] or "")) +
        "'>"

        "<label>Location</label>"
        "<input name='location' "
        "value='" +
        escape(str(row["location"] or "")) +
        "' required>"

        "<label>Complaint Type</label>"

        "<select name='complaint_type'>"

        +
        type_options
        +

        "</select>"

        "<label>Complaint Details</label>"
        "<textarea name='details'>" +
        escape(str(row["details"] or "")) +
        "</textarea>"

        "<label>Assigned Staff</label>"
        "<input name='assigned' "
        "value='" +
        escape(str(row["assigned"] or "")) +
        "'>"

        "<label>Status</label>"

        "<select name='status'>"

        +
        status_options
        +

        "</select>"

        "<label>Remarks</label>"
        "<textarea name='remarks'>" +
        escape(str(row["remarks"] or "")) +
        "</textarea>"

        "<button type='submit'>"
        "Update Complaint"
        "</button>"

        "</form>"

        "</div>"

        "<a class='button' href='/complaints'>"
        "Back to Complaints"
        "</a>"
    )

    conn.close()

    return page(
        "Edit Complaint",
        body
    )


# =========================================================
# DELETE COMPLAINT
# =========================================================

@app.route("/delete/<int:item_id>")
@admin_required
def delete(item_id):

    conn = db()

    conn.execute(
        "DELETE FROM complaints WHERE id=?",
        (item_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/complaints")


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
@login_required
def reports():

    date_from = request.args.get(
        "date_from",
        ""
    ).strip()

    date_to = request.args.get(
        "date_to",
        ""
    ).strip()

    status_filter = request.args.get(
        "status",
        ""
    ).strip()

    type_filter = request.args.get(
        "complaint_type",
        ""
    ).strip()

    conn = db()

    conditions = []
    values = []

    if date_from:

        conditions.append(
            "date >= ?"
        )

        values.append(
            date_from
        )

    if date_to:

        conditions.append(
            "date <= ?"
        )

        values.append(
            date_to
        )

    if status_filter:

        conditions.append(
            "status = ?"
        )

        values.append(
            status_filter
        )

    if type_filter:

        conditions.append(
            "complaint_type = ?"
        )

        values.append(
            type_filter
        )

    query = "SELECT * FROM complaints"

    if conditions:

        query += (
            " WHERE " +
            " AND ".join(conditions)
        )

    query += " ORDER BY date DESC, id DESC"

    rows = conn.execute(
        query,
        values
    ).fetchall()

    total = len(rows)

    pending = 0
    progress = 0
    completed = 0

    for r in rows:

        if r["status"] == "Pending":

            pending += 1

        elif r["status"] == "In Progress":

            progress += 1

        elif r["status"] == "Completed":

            completed += 1

    conn.close()

    table = ""

    for r in rows:

        table += (

            "<tr>"

            "<td>" +
            escape(str(r["complaint_no"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["date"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["time"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["complainant"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["location"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["complaint_type"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["assigned"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["status"] or "")) +
            "</td>"

            "<td>" +
            escape(str(r["remarks"] or "")) +
            "</td>"

            "</tr>"
        )

    if not table:

        table = (
            "<tr>"
            "<td colspan='9' "
            "style='text-align:center'>"
            "No complaints found."
            "</td>"
            "</tr>"
        )

    body = (

        "<div class='header'>"
        "<h1>Complaint Report</h1>"
        "</div>"

        "<div class='box no-print'>"

        "<h2>Report Filters</h2>"

        "<form method='GET'>"

        "<label>Date From</label>"
        "<input type='date' "
        "name='date_from' "
        "value='" +
        escape(date_from) +
        "'>"

        "<label>Date To</label>"
        "<input type='date' "
        "name='date_to' "
        "value='" +
        escape(date_to) +
        "'>"

        "<label>Status</label>"

        "<select name='status'>"

        "<option value=''>All Status</option>"

        "<option value='Pending' " +
        ("selected" if status_filter == "Pending" else "") +
        ">Pending</option>"

        "<option value='In Progress' " +
        ("selected" if status_filter == "In Progress" else "") +
        ">In Progress</option>"

        "<option value='Completed' " +
        ("selected" if status_filter == "Completed" else "") +
        ">Completed</option>"

        "</select>"

        "<label>Complaint Type</label>"

        "<select name='complaint_type'>"

        "<option value=''>All Types</option>"
        "<option value='Plumbing'>Plumbing</option>"
        "<option value='Carpenter'>Carpenter</option>"
        "<option value='Masonry'>Masonry</option>"
        "<option value='Painter'>Painter</option>"
        "<option value='Sewer'>Sewer</option>"
        "<option value='Metal Work'>Metal Work</option>"
        "<option value='Horticulture'>Horticulture</option>"
        "<option value='Electrical'>Electrical</option>"
        "<option value='Other'>Other</option>"

        "</select>"

        "<button type='submit'>"
        "Generate Report"
        "</button>"

        "</form>"

        "<a class='button gray' href='/reports'>"
        "Clear Filters"
        "</a>"

        "</div>"

        "<div class='box'>"

        "<div class='report-header'>"
        "<h1>Complaint Management Report</h1>"
        "<p>Generated Report</p>"
        "</div>"

        "<div class='report-info'>"

        "<b>Date From:</b> " +
        escape(date_from or "All") +

        "<br>"

        "<b>Date To:</b> " +
        escape(date_to or "All") +

        "<br>"

        "<b>Status:</b> " +
        escape(status_filter or "All") +

        "<br>"

        "<b>Complaint Type:</b> " +
        escape(type_filter or "All") +

        "</div>"

        "<div class='summary'>"

        "<div class='summary-box'>"
        "Total"
        "<div class='summary-number'>" +
        str(total) +
        "</div>"
        "</div>"

        "<div class='summary-box'>"
        "Pending"
        "<div class='summary-number'>" +
        str(pending) +
        "</div>"
        "</div>"

        "<div class='summary-box'>"
        "In Progress"
        "<div class='summary-number'>" +
        str(progress) +
        "</div>"
        "</div>"

        "<div class='summary-box'>"
        "Completed"
        "<div class='summary-number'>" +
        str(completed) +
        "</div>"
        "</div>"

        "</div>"

        "<div class='tablebox'>"

        "<table>"

        "<tr>"
        "<th>Complaint No.</th>"
        "<th>Date</th>"
        "<th>Time</th>"
        "<th>Complainant</th>"
        "<th>Location</th>"
        "<th>Type</th>"
        "<th>Assigned</th>"
        "<th>Status</th>"
        "<th>Remarks</th>"
        "</tr>"

        +
        table
        +

        "</table>"

        "</div>"

        "</div>"

        "<div class='no-print'>"

        "<button onclick='window.print()'>"
        "🖨️ Print / Save as PDF"
        "</button>"

        "<a class='button' href='/'>"
        "Back to Dashboard"
        "</a>"

        "</div>"
    )

    return page(
        "Reports",
        body
    )


# =========================================================
# USER MANAGEMENT
# =========================================================

@app.route("/users")
@admin_required
def users():

    conn = db()

    rows = conn.execute(
        "SELECT id, username, role FROM users ORDER BY id"
    ).fetchall()

    conn.close()

    table = ""

    for r in rows:

        delete_button = ""

        if r["username"] != "admin":

            delete_button = (

                "<a class='action delete' "
                "href='/delete_user/" +
                str(r["id"]) +
                "' "
                "onclick=\"return confirm('Delete this user?')\">"
                "Delete"
                "</a>"
            )

        table += (

            "<tr>"

            "<td>" +
            str(r["id"]) +
            "</td>"

            "<td>" +
            escape(str(r["username"])) +
            "</td>"

            "<td>" +
            escape(str(r["role"])) +
            "</td>"

            "<td>" +
            delete_button +
            "</td>"

            "</tr>"
        )

    body = (

        "<div class='header'>"
        "<h1>User Management</h1>"
        "</div>"

        "<div class='box'>"

        "<h2>Add New User</h2>"

        "<form method='POST' action='/add_user'>"

        "<label>Username</label>"
        "<input name='username' required>"

        "<label>Password</label>"
        "<input type='password' name='password' required>"

        "<label>Role</label>"

        "<select name='role'>"
        "<option>User</option>"
        "<option>Admin</option>"
        "</select>"

        "<button type='submit'>"
        "Create User"
        "</button>"

        "</form>"

        "</div>"

        "<div class='box'>"

        "<h2>Existing Users</h2>"

        "<div class='tablebox'>"

        "<table>"

        "<tr>"
        "<th>ID</th>"
        "<th>Username</th>"
        "<th>Role</th>"
        "<th>Action</th>"
        "</tr>"

        +
        table
        +

        "</table>"

        "</div>"
        "</div>"

        "<a class='button' href='/'>"
        "Back to Dashboard"
        "</a>"
    )

    return page(
        "User Management",
        body
    )


# =========================================================
# ADD USER
# =========================================================

@app.route(
    "/add_user",
    methods=["POST"]
)
@admin_required
def add_user():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    role = request.form.get(
        "role",
        "User"
    )

    if role not in ["User", "Admin"]:

        role = "User"

    if not username or not password:

        return page(
            "Error",
            """
            <div class='box center'>
                <h2>Username and password are required.</h2>
            </div>

            <a class='button' href='/users'>
                Back to Users
            </a>
            """
        )

    conn = db()

    try:

        conn.execute(
            """
            INSERT INTO users
            (username, password, role)
            VALUES (?, ?, ?)
            """,
            (
                username,
                password,
                role
            )
        )

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return page(
            "Error",
            """
            <div class='box center'>
                <h2>Username already exists.</h2>
            </div>

            <a class='button' href='/users'>
                Back to Users
            </a>
            """
        )

    conn.close()

    return redirect("/users")


# =========================================================
# DELETE USER
# =========================================================

@app.route(
    "/delete_user/<int:user_id>"
)
@admin_required
def delete_user(user_id):

    conn = db()

    user = conn.execute(
        "SELECT id, username FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    if user is not None:

        if user["username"] != "admin":

            conn.execute(
                "DELETE FROM users WHERE id=?",
                (user_id,)
            )

            conn.commit()

    conn.close()

    return redirect("/users")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )