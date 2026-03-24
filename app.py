from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils.data_processing import process_form_input, get_weather_advice, is_valid_constituency
from utils.predictor import recommend_crop, predict_price_trend
import os
import pymysql

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_demo'

# Ensure directories exist
app.template_folder = os.path.abspath('templates')
app.static_folder = os.path.abspath('static')

# ----------------- MYSQL CONFIGURATION -----------------
# Update these credentials if your local MySQL setup requires a password
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '#MySQL123' 
DB_NAME = 'crop_advisory'

def get_db_connection(with_db=True):
    """Establish a connection to MySQL, optionally selecting the database."""
    if with_db:
        return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    else:
        return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Setup DB
def init_db():
    # 1. Connect without selecting a database specifically to create it if it doesn't exist
    try:
        conn = get_db_connection(with_db=False)
        c = conn.cursor()
        c.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError as e:
        print(f"Failed to connect to MySQL: {e}")
        return

    # 2. Connect to the actual database to generate tables
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, username VARCHAR(255) UNIQUE, password VARCHAR(255))''')
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, 
                  user_id INTEGER, 
                  location VARCHAR(255), 
                  soil VARCHAR(255), 
                  season VARCHAR(255), 
                  water VARCHAR(255), 
                  crop VARCHAR(255), 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

init_db()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user_row = c.fetchone()
    conn.close()
    if user_row:
        return User(id=user_row[0], username=user_row[1])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except pymysql.err.IntegrityError:
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
        c.execute("SELECT * FROM users WHERE username=%s", (username,))
        user_row = c.fetchone()
        conn.close()
        
        if user_row and check_password_hash(user_row[2], password):
            user = User(id=user_row[0], username=user_row[1])
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

@app.route('/')
def home():
    return render_template('index.html')

from utils.data_processing import AP_CONSTITUENCIES

@app.route('/form')
@login_required
def form():
    return render_template('form.html', constituencies=AP_CONSTITUENCIES)

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if request.method == 'POST':
        form_data = request.form
        
        # 0. Validate Andhra Pradesh Constituency
        raw_location = form_data.get('location', '')
        if not is_valid_constituency(raw_location):
            flash(f"Sorry, '{raw_location}' was not recognized as an officially listed AP Constituency. Check your selection.", "danger")
            return redirect(url_for('form'))
        
        # 1. Process inputs
        processed_data = process_form_input(form_data)
        
        # 2. Get Crop Recommendations
        top_crops = recommend_crop(
            soil=processed_data['soil'],
            season=processed_data['season'],
            water=processed_data['water']
        )
        
        # The primary recommended crop
        best_crop = top_crops[0][0] if top_crops else "Unknown"
        confidence = top_crops[0][1] if top_crops else 0
        
        # 3. Get Price Trend for the top crop
        price_trend = predict_price_trend(best_crop)
        
        # 4. Get Weather Advice
        weather_advice = get_weather_advice(processed_data['location'])
        
        # 5. Save exactly this run into history
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""INSERT INTO history (user_id, location, soil, season, water, crop)
                     VALUES (%s, %s, %s, %s, %s, %s)""", 
                  (current_user.id, raw_location.capitalize(), form_data.get('soil'), form_data.get('season'), form_data.get('water'), best_crop))
        conn.commit()
        conn.close()
        
        # Combine all data for the final decision panel
        decision_data = {
            'location': processed_data['location'].capitalize(),
            'grow': best_crop,
            'confidence': confidence,
            'alternatives': top_crops[1:],
            'best_selling_time': price_trend.get('best_month', 'N/A'),
            'expected_price': price_trend.get('expected_price', 'N/A'),
            'price_trend_labels': price_trend.get('labels', []),
            'price_trend_data': price_trend.get('prices', []),
            'weather_advice': weather_advice,
            # Pass original form data back to result so Edit button can use it
            'original_soil': form_data.get('soil', ''),
            'original_season': form_data.get('season', ''),
            'original_water': form_data.get('water', '')
        }
        
        return render_template('result.html', result=decision_data)

@app.route('/history')
@login_required
def history():
    conn = get_db_connection()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute("SELECT * FROM history WHERE user_id=%s ORDER BY timestamp DESC", (current_user.id,))
    records = c.fetchall()
    conn.close()
    return render_template('history.html', records=records)

@app.route('/history/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_history(record_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE id=%s AND user_id=%s", (record_id, current_user.id))
    conn.commit()
    conn.close()
    flash('Record deleted successfully.', 'success')
    return redirect(url_for('history'))

@app.route('/history/view/<int:record_id>')
@login_required
def view_history(record_id):
    conn = get_db_connection()
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute("SELECT * FROM history WHERE id=%s AND user_id=%s", (record_id, current_user.id))
    record = c.fetchone()
    conn.close()
    
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('history'))

    # We must process the historical raw string inputs into encoded ints for the ML model
    mock_form_data = {
        'location': record['location'],
        'soil': record['soil'],
        'season': record['season'],
        'water': record['water']
    }
    processed_data = process_form_input(mock_form_data)

    # Re-fetch contextual ML data but skip saving to history again
    top_crops = recommend_crop(soil=processed_data['soil'], season=processed_data['season'], water=processed_data['water'])
    best_crop = record['crop']
    confidence = top_crops[0][1] if top_crops else 0
    price_trend = predict_price_trend(best_crop)
    weather_advice = get_weather_advice(record['location'])
    
    decision_data = {
        'location': record['location'],
        'grow': best_crop,
        'confidence': confidence,
        'alternatives': top_crops[1:],
        'best_selling_time': price_trend.get('best_month', 'N/A'),
        'expected_price': price_trend.get('expected_price', 'N/A'),
        'price_trend_labels': price_trend.get('labels', []),
        'price_trend_data': price_trend.get('prices', []),
        'weather_advice': weather_advice,
        'original_soil': record['soil'],
        'original_season': record['season'],
        'original_water': record['water']
    }
    return render_template('result.html', result=decision_data)

if __name__ == '__main__':
    app.run(debug=True)
