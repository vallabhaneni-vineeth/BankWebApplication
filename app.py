
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="user_management",
        user="postgres",
        password="Vineeth@1234"
    )

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            if user:
                session['user'] = username
                flash('Login successful!')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.')
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return render_template('login.html')

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

# Route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists.')
            else:
                cursor.execute("INSERT INTO users (username, password, balance) VALUES (%s, %s, %s)", (username, password, 0))
                conn.commit()
                flash('Registration successful. Please log in.')
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    return render_template('register.html')

# Route for the main banking operations
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    username = session['user']
    conn = None
    cursor = None
    user_balance = Decimal(0)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT balance FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            user_balance = Decimal(result['balance'] or 0)

        if request.method == 'POST':
            action = request.form.get('action')

            # Only parse and validate amount for Deposit or Withdraw actions
            if action in ['Deposit', 'Withdraw']:
                amount = request.form.get('amount', type=float)
                if amount is None:  # Ensure amount is provided for these actions
                    flash('Please enter an amount.')
                    return redirect(url_for('index'))  # Redirect to avoid processing
                amount = Decimal(amount)

                if action == 'Deposit':
                    if amount <= 0:
                        flash('Invalid deposit amount.')
                    else:
                        user_balance += amount
                        cursor.execute("UPDATE users SET balance = %s WHERE username = %s", (user_balance, username))
                        conn.commit()
                        flash(f"Rs {amount:.2f} deposited successfully.")
                elif action == 'Withdraw':
                    if amount <= 0:
                        flash('Invalid withdrawal amount.')
                    elif amount > user_balance:
                        flash('Insufficient balance.')
                    else:
                        user_balance -= amount
                        cursor.execute("UPDATE users SET balance = %s WHERE username = %s", (user_balance, username))
                        conn.commit()
                        flash(f"Rs {amount:.2f} withdrawn successfully.")
            elif action == 'Check Balance':  # This skips amount entirely
                flash(f"Your current balance is: Rs {user_balance:.2f}")
    except Exception as e:
        flash(f"An error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('index.html', balance=user_balance)


if __name__ == '__main__':
    app.run(debug=True)

