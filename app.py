from flask import Flask, render_template, request, redirect, session
import mysql.connector
from datetime import date
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")


def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "2627"),
        database=os.environ.get("DB_NAME", "maintenance_db")
    )


# ---------------- decorators ----------------

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrap


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user' not in session or session.get("role") != "admin":
            return redirect('/')
        return f(*args, **kwargs)
    return wrap


# ---------------- login ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid login")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- home ----------------

@app.route('/')
@login_required
def index():

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM equipment")
    equipment = cur.fetchall()
    conn.close()

    return render_template(
        "index.html",
        equipment=equipment,
        role=session['role']
    )


# ---------------- add equipment (admin) ----------------

@app.route('/add_equipment', methods=['GET', 'POST'])
@admin_required
def add_equipment():

    if request.method == 'POST':

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO equipment(name,type,location,status) VALUES(%s,%s,%s,%s)",
            (
                request.form['name'],
                request.form['type'],
                request.form['location'],
                request.form['status']
            )
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add_equipment.html')


# ---------------- delete equipment (admin) ----------------

@app.route('/delete/<int:id>')
@admin_required
def delete_equipment(id):

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM equipment WHERE id=%s", (id,))
    conn.commit()
    conn.close()

    return redirect('/')


# ---------------- mark working (admin) ----------------

@app.route('/mark_working/<int:id>')
@admin_required
def mark_working(id):

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE equipment SET status='Working' WHERE id=%s",
        (id,)
    )
    conn.commit()
    conn.close()

    return redirect('/')


# ---------------- add log (admin) ----------------

@app.route('/add_log/<int:id>', methods=['GET', 'POST'])
@admin_required
def add_log(id):

    if request.method == 'POST':

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO maintenance_log(equipment_id,log_date,fault,action_taken,technician) VALUES(%s,%s,%s,%s,%s)",
            (
                id,
                date.today(),
                request.form['fault'],
                request.form['action'],
                request.form['technician']
            )
        )

        cur.execute(
            "UPDATE equipment SET status='Under Maintenance' WHERE id=%s",
            (id,)
        )

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('add_log.html', equipment_id=id)


# ---------------- view logs (all users) ----------------

@app.route('/logs/<int:id>')
@login_required
def view_logs(id):

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM maintenance_log WHERE equipment_id=%s",
        (id,)
    )
    logs = cur.fetchall()
    conn.close()

    return render_template('logs.html', logs=logs)


if __name__ == "__main__":
    app.run(debug=True)