from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')  # Use secure key in production

# Configure session to use filesystem
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Database configuration from environment variables (Render)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "auth_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "root")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    return conn

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            message = "Please fill out both fields"
            return render_template('register.html', message=message)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()

        if user:
            message = "Username already exists"
        else:
            hashed_password = generate_password_hash(password)
            cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
            conn.commit()
            return redirect(url_for('login'))

        cur.close()
        conn.close()

    return render_template('register.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            message = "Invalid username or password"

    return render_template('login.html', message=message)

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Only for local testing (not used in Render deployment)
if __name__ == '__main__':
    app.run(debug=True)
