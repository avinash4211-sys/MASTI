# app.py
from flask import Flask, render_template, request, redirect, send_file, session
import sqlite3, pandas as pd

app = Flask(__name__)
app.secret_key = "mysecretkey123"
DB='data.db'

# ---------- DB ----------

def init_db():
    conn=sqlite3.connect(DB)
    c=conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        money_from TEXT,
        amount REAL,
        AK REAL,
        DY REAL,
        RK REAL,
        NP REAL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS receivable(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        party TEXT,
        amount REAL,
        note TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# ---------- LOGIN ----------
USER = "masti"
PASS = "bakchodi"

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

# ---------- MAIN PAGE ----------

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    conn=sqlite3.connect(DB)
    rows=conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()

    total_amount=sum(r[3] for r in rows) if rows else 0
    totals=[sum(r[i] for r in rows) for i in range(4,8)] if rows else [0,0,0,0]
    equal= total_amount/4 if total_amount else 0
    balances=[round(t-equal,2) for t in totals]

    conn.close()
    return render_template('index.html', rows=rows, total_amount=total_amount, totals=totals, equal=equal, balances=balances)

@app.route('/add', methods=['POST'])
def add():
    if 'user' not in session:
        return redirect('/login')
    data=request.form
    conn=sqlite3.connect(DB)
    conn.execute("INSERT INTO records(date,money_from,amount,AK,DY,RK,NP) VALUES(?,?,?,?,?,?,?)",
                 (data['date'],data['from'],data['amount'],data['AK'],data['DY'],data['RK'],data['NP']))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------- EDIT ----------

@app.route('/edit/<int:id>')
def edit(id):
    if 'user' not in session:
        return redirect('/login')
    conn=sqlite3.connect(DB)
    row=conn.execute("SELECT * FROM records WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('edit.html', r=row)

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    if 'user' not in session:
        return redirect('/login')
    d=request.form
    conn=sqlite3.connect(DB)
    conn.execute("""UPDATE records SET date=?,money_from=?,amount=?,AK=?,DY=?,RK=?,NP=? WHERE id=?""",
                 (d['date'],d['from'],d['amount'],d['AK'],d['DY'],d['RK'],d['NP'],id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect('/login')
    conn=sqlite3.connect(DB)
    conn.execute("DELETE FROM records WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------- RECEIVABLE ----------

@app.route('/receivable')
def receivable():
    if 'user' not in session:
        return redirect('/login')
    conn=sqlite3.connect(DB)
    rows=conn.execute("SELECT * FROM receivable ORDER BY id DESC").fetchall()
    total_receivable = sum(r[3] for r in rows) if rows else 0
    conn.close()
    return render_template('receivable.html', rows=rows, total_receivable=total_receivable)

@app.route('/add_receivable', methods=['POST'])
def add_receivable():
    if 'user' not in session:
        return redirect('/login')
    d=request.form
    conn=sqlite3.connect(DB)
    conn.execute("INSERT INTO receivable(date,party,amount,note) VALUES(?,?,?,?)",
                 (d['date'],d['party'],d['amount'],d['note']))
    conn.commit()
    conn.close()
    return redirect('/receivable')

# ---------- EXPORT ----------

@app.route('/export')
def export():
    if 'user' not in session:
        return redirect('/login')
    conn=sqlite3.connect(DB)
    df=pd.read_sql_query("SELECT date,money_from,amount,AK,DY,RK,NP,(AK+DY+RK+NP) as total_taken FROM records",conn)
    conn.close()
    file='export.xlsx'
    df.to_excel(file,index=False)
    return send_file(file,as_attachment=True)

if __name__=='__main__':
    app.run(debug=True)