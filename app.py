from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils.data_processing import process_form_input, get_weather_advice, is_valid_constituency, AP_CONSTITUENCIES
from utils.predictor import recommend_crop, predict_price_trend
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_demo'

# ----------------- SQLITE CONFIG -----------------
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  location TEXT,
                  soil TEXT,
                  season TEXT,
                  water TEXT,
                  crop TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()

init_db()

# ----------------- LOGIN SETUP -----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user_row = c.fetchone()
    conn.close()
    if user_row:
        return User(id=user_row["id"], username=user_row["username"])
    return None

# ----------------- ROUTES -----------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user_row = c.fetchone()
        conn.close()

        if user_row and check_password_hash(user_row["password"], password):
            user = User(id=user_row["id"], username=user_row["username"])
            login_user(user)
            return redirect(url_for('form'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/form')
@login_required
def form():
    return render_template('form.html', constituencies=AP_CONSTITUENCIES)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    form_data = request.form

    raw_location = form_data.get('location', '')
    if not is_valid_constituency(raw_location):
        flash(f"'{raw_location}' is not a valid AP Constituency.", "danger")
        return redirect(url_for('form'))

    processed_data = process_form_input(form_data)

    top_crops = recommend_crop(
        soil=processed_data['soil'],
        season=processed_data['season'],
        water=processed_data['water']
    )

    best_crop = top_crops[0][0] if top_crops else "Unknown"
    confidence = top_crops[0][1] if top_crops else 0

    price_trend = predict_price_trend(best_crop)
    weather_advice = get_weather_advice(processed_data['location'])

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO history (user_id, location, soil, season, water, crop)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (current_user.id, raw_location, form_data.get('soil'),
               form_data.get('season'), form_data.get('water'), best_crop))
    conn.commit()
    conn.close()

    decision_data = {
        'location': processed_data['location'],
        'grow': best_crop,
        'confidence': confidence,
        'alternatives': top_crops[1:],
        'best_selling_time': price_trend.get('best_month', 'N/A'),
        'expected_price': price_trend.get('expected_price', 'N/A'),
        'price_trend_labels': price_trend.get('labels', []),
        'price_trend_data': price_trend.get('prices', []),
        'weather_advice': weather_advice,
        'original_soil': form_data.get('soil'),
        'original_season': form_data.get('season'),
        'original_water': form_data.get('water')
    }

    return render_template('result.html', result=decision_data)

@app.route('/history')
@login_required
def history():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE user_id=? ORDER BY timestamp DESC", (current_user.id,))
    records = c.fetchall()
    conn.close()
    return render_template('history.html', records=records)

# ----------------- RUN -----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)