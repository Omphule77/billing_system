from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
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
    return redirect(url_for('main.login'))

@bp.route('/dashboard/<int:id>')
def dashboard(id):
    try:
        db=get_db_connection()
        cursor=db.cursor(dictionary=True)

        query="select * from registration where id=%s"
        cursor.execute(query,(id,))
        user=cursor.fetchone()
        cursor.close()
        db.close()
        print(f"success user found: {user}")
        return render_template('dashboard.html',user=user)

    except Exception as e:
        print(f"Error found: {e}")
        return render_template('dashboard.html')

@bp.route('/inventory/<int:id>')
def inventory(id):
    try:
        db=get_db_connection()
        cursor=db.cursor(dictionary=True)

        query="select * from registration where id=%s"
        cursor.execute(query,(id,))
        user=cursor.fetchone()

        q="select * from inventory_item"
        cursor.execute(q)
        items=cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('inventory.html', user=user, items=items)

    except Exception as e:
        print(f"Error found: {e}")
        return render_template('inventory.html')


@bp.route('/add_inventory_item/<int:id>', methods=['GET', 'POST'])
def add_inventory_item(id):
    if request.method=='POST':
        item_name=request.form['item_name']
        category=request.form['category']
        price=request.form['price']
        unit=request.form['unit']
        quantity=request.form['quantity']
        status=request.form['status']

        try:
            db=get_db_connection()
            cursor=db.cursor(dictionary=True)

            query="select * from registration where id=%s"
            cursor.execute(query,(id,))
            user=cursor.fetchone()

            q="insert into inventory_item(item_name,category,price,unit,quantity,status) values(%s,%s,%s,%s,%s,%s)"
            cursor.execute(q,(item_name,category,price,unit,quantity,status))
            db.commit()
            cursor.close() 
            db.close()
            flash('Inventory item added successfully!', 'success')
            return redirect(url_for('main.inventory', user=user))

        except Exception as e: 
            print(f"Error found: {e}")
            flash('Failed to add inventory item!', 'danger')
            return redirect(url_for('main.inventory', id=id))
    else:
        try:
            db=get_db_connection()
            cursor=db.cursor(dictionary=True)

            query="select * from registration where id=%s"
            cursor.execute(query,(id,))
            user=cursor.fetchone()
            cursor.close()
            db.close()
            return render_template('add_inventory_item.html', user=user)
        except Exception as e:
            print(f"Error found: {e}")
            return redirect(url_for('main.inventory', id=id))
    

@bp.route('/bill')
def bill():
    return render_template('bill.html')

@bp.route('/create_bill/<int:id>')
def create_bill(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "select * from registration where id=%s"
        cursor.execute(query, (id,))
        user = cursor.fetchone()

        q="select * from hotel"
        cursor.execute(q)
        hotel=cursor.fetchall()
        
        cursor.close()
        db.close()
        return render_template('create_bill.html', user=user,hotel=hotel)
    except Exception as e:
        print(f"Error in create_bill: {e}")
        return render_template('create_bill.html')

@bp.route('/add_item/<int:id>/<int:hotel_id>')
def add_item(id,hotel_id):
    try:
        db=get_db_connection()
        cursor=db.cursor(dictionary=True)

        query="select * from registration where id=%s"
        cursor.execute(query,(id,))
        user=cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('add_item.html',user=user)
    except Exception as e:
        print(f"Error in add_item: {e}")
        return redirect(url_for('main.create_bill', id=id))

@bp.route('/add_hotel/<int:id>',methods=['GET','POST'])
def add_hotel(id):
    if request.method=='POST':
        name=request.form['owner_name']
        mobile=request.form['mobile']
        email=request.form['email']
        hotel_name=request.form['hotel_name']
        address=request.form['address']
        
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            query = "insert into hotel(owner_name,mobile,email,hotel_name,address) values(%s,%s,%s,%s,%s)"
            cursor.execute(query,(name,mobile,email,hotel_name,address))
            db.commit()
            cursor.close()
            db.close()
            flash('Hotel added successfully!', 'success')
            return redirect(url_for('main.create_bill', id=id))
        except Exception as e:
            print(f"Error in add_hotel: {e}")
            flash('Failed to add hotel!', 'danger')
            return redirect(url_for('main.create_bill', id=id))
    else:
        try:
            db=get_db_connection()
            cursor=db.cursor(dictionary=True)

            query="select * from registration where id=%s"
            cursor.execute(query,(id,))
            user=cursor.fetchone()
            cursor.close()
            db.close()
            return render_template('add_hotel.html',user=user)
        except Exception as e:
            print(f"Error in add_hotel: {e}")
            return redirect(url_for('main.create_bill', id=id))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            
            # Query to fetch user by email
            query = "SELECT * FROM registration WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            
            cursor.close()
            db.close()
            
            if user:
                if user['password'] == password:
                    flash('Login successful!', 'success')
                    return redirect(url_for('main.dashboard',id=user['id']))
                else:
                     flash('Invalid email or password', 'danger')
            else:
                flash('Invalid email or password', 'danger')
                
        except Exception as e:
            print(f"DEBUG: Error during login: {e}")
            flash(f'An error occurred: {e}', 'danger')

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
