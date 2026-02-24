from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from config import DB_CONFIG
from database import create_database_and_table
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this'

# Initialize database
create_database_and_table()

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid username or password')
        
        except Exception as e:
            return render_template('login.html', error=f'Error: {str(e)}')
        
        finally:
            cursor.close()
            connection.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            connection.commit()
            return redirect(url_for('login'))
        
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry
                return render_template('register.html', error='Username or email already exists')
            else:
                return render_template('register.html', error=f'Error: {str(err)}')
        
        finally:
            cursor.close()
            connection.close()
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)