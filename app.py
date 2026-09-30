from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
import csv
import io
from datetime import date

app = Flask(__name__)
DB = "expenses.db"
CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Education", "Health", "Other"]

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        expense_date TEXT NOT NULL,
        notes TEXT DEFAULT ''
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""")
    conn.execute("INSERT OR IGNORE INTO settings VALUES ('monthly_budget','10000')")
    conn.commit()
    conn.close()

def get_budget():
    conn = db()
    row = conn.execute("SELECT value FROM settings WHERE key='monthly_budget'").fetchone()
    conn.close()
    return float(row["value"])

@app.route("/")
def index():
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "")

    conn = db()
    query = "SELECT * FROM expenses WHERE substr(expense_date,1,7)=?"
    params = [month]

    if search:
        query += " AND (title LIKE ? OR notes LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if category:
        query += " AND category=?"
        params.append(category)

    expenses = conn.execute(
        query + " ORDER BY expense_date DESC, id DESC", params
    ).fetchall()

    total = conn.execute(
        "SELECT COALESCE(SUM(amount),0) total FROM expenses WHERE substr(expense_date,1,7)=?",
        (month,)
    ).fetchone()["total"]

    categories = conn.execute(
        """SELECT category, ROUND(SUM(amount),2) total
           FROM expenses WHERE substr(expense_date,1,7)=?
           GROUP BY category ORDER BY total DESC""",
        (month,)
    ).fetchall()
    conn.close()

    budget = get_budget()
    return render_template(
        "index.html",
        expenses=expenses,
        total=float(total),
        budget=budget,
        remaining=budget-float(total),
        month=month,
        categories=CATEGORIES,
        category_data=[dict(x) for x in categories],
        selected_category=category,
        search=search
    )

@app.post("/add")
def add():
    amount = float(request.form["amount"])
    conn = db()
    conn.execute(
        "INSERT INTO expenses(title,amount,category,expense_date,notes) VALUES(?,?,?,?,?)",
        (request.form["title"].strip(), amount, request.form["category"],
         request.form["expense_date"], request.form.get("notes","").strip())
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.post("/delete/<int:item_id>")
def delete(item_id):
    conn = db()
    conn.execute("DELETE FROM expenses WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for("index"))

@app.post("/budget")
def budget():
    value = max(0, float(request.form["budget"]))
    conn = db()
    conn.execute("UPDATE settings SET value=? WHERE key='monthly_budget'", (str(value),))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for("index"))

@app.get("/export")
def export():
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    conn = db()
    rows = conn.execute(
        "SELECT title,amount,category,expense_date,notes FROM expenses "
        "WHERE substr(expense_date,1,7)=? ORDER BY expense_date DESC",
        (month,)
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Title","Amount","Category","Date","Notes"])
    for r in rows:
        writer.writerow([r["title"],r["amount"],r["category"],r["expense_date"],r["notes"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=expenses-{month}.csv"}
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
