# ===== app.py (Full working safe version for Render + Postgres) =====

from flask import Flask, render_template, request, redirect, url_for
import psycopg2, os, logging, sys, traceback

# ---------- LOGGING (shows real errors in Render logs) ----------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)

# ---------- DATABASE ----------

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

# Safe number converter (prevents blank page crashes)

def num(v):
    try:
        return float(v or 0)
    except:
        return 0

# ---------- INIT TABLE ----------

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ledger(
        id SERIAL PRIMARY KEY,
        name TEXT,
        credit NUMERIC,
        debit NUMERIC
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS receivable(
        id SERIAL PRIMARY KEY,
        name TEXT,
        amount NUMERIC
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name, credit, debit FROM ledger ORDER BY id DESC")
    rows = cur.fetchall()

    total = 0
    for r in rows:
        total += num(r[1]) - num(r[2])

    cur.close()
    conn.close()
    return f"Total Balance: {total}"

# ---------- ADD ENTRY ----------
@app.route('/add', methods=['POST'])
def add():
    name = request.form.get('name')
    credit = num(request.form.get('credit'))
    debit = num(request.form.get('debit'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO ledger(name, credit, debit) VALUES(%s,%s,%s)", (name, credit, debit))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('index'))

# ---------- RECEIVABLE ----------
@app.route('/receivable')
def receivable_page():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, amount FROM receivable")
    rows = cur.fetchall()

    total = sum(num(r[1]) for r in rows)

    cur.close()
    conn.close()
    return f"Total Expected Receivable: {total}"

@app.route('/add_receivable', methods=['POST'])
def add_receivable():
    name = request.form.get('name')
    amount = num(request.form.get('amount'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO receivable(name, amount) VALUES(%s,%s)", (name, amount))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('receivable_page'))

# ---------- GLOBAL ERROR HANDLER ----------
@app.errorhandler(Exception)
def handle_exception(e):
    print("\n\n===== APP CRASH =====")
    traceback.print_exc()
    print("=====================\n\n")
    return "Server Error — check Render logs", 500
