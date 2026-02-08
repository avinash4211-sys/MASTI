# app.py (PostgreSQL version - fixed numeric crash)
from flask import Flask, render_template, request, redirect, send_file, session
import pandas as pd
import os, psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = "mysecretkey123"

# ---------- DB CONNECTION ----------
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    url = urlparse(DATABASE_URL)
    return psycopg2.connect(
        host=url.hostname,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        port=url.port
    )

# ---------- INIT DB ----------

def init_db():
    conn=get_conn()
    cur=conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS records(
        id SERIAL PRIMARY KEY,
        date TEXT,
        money_from TEXT,
        amount FLOAT,
        AK FLOAT,
        DY FLOAT,
        RK FLOAT,
        NP FLOAT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS receivable(
        id SERIAL PRIMARY KEY,
        date TEXT,
        party TEXT,
        amount FLOAT,
        note TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
USER = "admin"
PASS = "1234"

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['username']==USER and request.form['password']==PASS:
            session['user']='ok'
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid Login")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/login')

# ---------- MAIN ----------
@app.route('/')
def index():
    if 'user' not in session: return redirect('/login')

    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM records ORDER BY id DESC")
    rows=cur.fetchall()

    def num(v):
        try: return float(v or 0)
        except: return 0

    total_amount=sum(num(r[3]) for r in rows)
    totals=[sum(num(r[i]) for r in rows) for i in range(4,8)]
    equal= total_amount/4 if total_amount else 0
    balances=[round(t-equal,2) for t in totals]

    conn.close()
    return render_template('index.html', rows=rows, total_amount=total_amount, totals=totals, equal=equal, balances=balances)

@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session: return redirect('/login')
    d=request.form
    conn=get_conn(); cur=conn.cursor()
    cur.execute("INSERT INTO records(date,money_from,amount,AK,DY,RK,NP) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                 (d['date'],d['from'],d['amount'],d['AK'],d['DY'],d['RK'],d['NP']))
    conn.commit(); conn.close()
    return redirect('/')

@app.route('/edit/<int:id>')
def edit(id):
    if 'user' not in session: return redirect('/login')
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM records WHERE id=%s", (id,))
    row=cur.fetchone(); conn.close()
    return render_template('edit.html', r=row)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    if 'user' not in session: return redirect('/login')
    d=request.form
    conn=get_conn(); cur=conn.cursor()
    cur.execute("""UPDATE records SET date=%s,money_from=%s,amount=%s,AK=%s,DY=%s,RK=%s,NP=%s WHERE id=%s""",
                (d['date'],d['from'],d['amount'],d['AK'],d['DY'],d['RK'],d['NP'],id))
    conn.commit(); conn.close()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session: return redirect('/login')
    conn=get_conn(); cur=conn.cursor()
    cur.execute("DELETE FROM records WHERE id=%s", (id,))
    conn.commit(); conn.close()
    return redirect('/')

# ---------- RECEIVABLE ----------
@app.route('/receivable')
def receivable():
    if 'user' not in session: return redirect('/login')
    conn=get_conn(); cur=conn.cursor()
    cur.execute("SELECT * FROM receivable ORDER BY id DESC")
    rows=cur.fetchall()
    total_receivable=sum(float(r[3] or 0) for r in rows)
    conn.close()
    return render_template('receivable.html', rows=rows, total_receivable=total_receivable)

@app.route('/add_receivable', methods=['POST'])
def add_receivable():
    if 'user' not in session: return redirect('/login')
    d=request.form
    conn=get_conn(); cur=conn.cursor()
    cur.execute("INSERT INTO receivable(date,party,amount,note) VALUES(%s,%s,%s,%s)",(d['date'],d['party'],d['amount'],d['note']))
    conn.commit(); conn.close()
    return redirect('/receivable')

# ---------- EXPORT ----------
@app.route('/export')
def export():
    if 'user' not in session: return redirect('/login')
    conn=get_conn()
    df=pd.read_sql_query("SELECT date,money_from,amount,AK,DY,RK,NP,(AK+DY+RK+NP) as total_taken FROM records",conn)
    conn.close()
    file='export.xlsx'
    df.to_excel(file,index=False)
    return send_file(file,as_attachment=True)

if __name__=='__main__':
    app.run(debug=True)
