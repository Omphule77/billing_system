from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import mysql.connector

bp = Blueprint('main', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=current_app.config['MYSQL_HOST'],
        user=current_app.config['MYSQL_USER'],
        password=current_app.config['MYSQL_PASSWORD'],
        database=current_app.config['MYSQL_DB']
    )



@bp.route('/')
def index():
    return render_template('base.html')

@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@bp.route('/bill')
def bill():
    return render_template('bill.html')

@bp.route('/create_bill')
def create_bill():
    return render_template('create_bill.html')

@bp.route('/add_item')
def add_item():
    return render_template('add_item.html')

@bp.route('/login')
def login():
    return render_template('login.html')

@bp.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']

        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            # Using table name 'registration' as requested
            query = "INSERT INTO registration (name, mobile, email, address, password) VALUES (%s, %s, %s, %s, %s)"
            print(f"DEBUG: Executing INSERT into 'registration' for user: {name}") 
            cursor.execute(query, (name, mobile, email, address, password))
            db.commit()
            print(f"DEBUG: Commit successful. Row ID: {cursor.lastrowid}")
            
            cursor.close()
            db.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            print(f"DEBUG: Error during registration: {e}") # Printing error to terminal
            flash(f'An error occurred: {e}', 'danger')
            return render_template('registration.html')
    return render_template('registration.html')
