from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
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
    

@bp.route('/update_inventory_item/<int:item_id>', methods=['POST'])
def update_inventory_item(item_id):
    try:
        data = request.get_json()
        price = data.get('price')
        quantity = data.get('quantity')
        status = data.get('status')

        db = get_db_connection()
        cursor = db.cursor()
        
        query = "UPDATE inventory_item SET price=%s, quantity=%s, status=%s WHERE item_id=%s"
        cursor.execute(query, (price, quantity, status, item_id))
        db.commit()
        
        cursor.close()
        db.close()
        
        return jsonify({'success': True, 'message': 'Item updated successfully'})
    except Exception as e:
        print(f"Error updating item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/bill/<int:id>/<int:hotel_id>/<int:bill_no>')
def bill(id, hotel_id, bill_no):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get User
        query = "select * from registration where id=%s"
        cursor.execute(query, (id,))
        user = cursor.fetchone()

        # Get Hotel
        q = "select * from hotel where id=%s"
        cursor.execute(q, (hotel_id,))
        hotel = cursor.fetchone()

        # Get Items
        item_query = "select * from item_bill where bill_no=%s"
        cursor.execute(item_query, (bill_no,))
        items = cursor.fetchall()

        cursor.close()
        db.close()
        return render_template('bill.html', user=user, hotel=hotel, items=items, bill_no=bill_no)
    except Exception as e:
        print(f"Error in bill generation: {e}")
        return redirect(url_for('main.create_bill', id=id))

@bp.route('/create_bill/<int:id>')
def create_bill(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = "select * from registration where id=%s"
        cursor.execute(query, (id,))
        user = cursor.fetchone()

        bill_query="select max(bill_no) as bill_no from item_bill"
        cursor.execute(bill_query)
        result=cursor.fetchone()
        next_bill_no = (result['bill_no'] or 0) + 1

        next_bill_no = (result['bill_no'] or 0) + 1

        search = request.args.get('search')
        if search:
            q="select * from hotel where hotel_name like %s"
            cursor.execute(q, (f"%{search}%",))
        else:
            q="select * from hotel"
            cursor.execute(q)
            
        hotel=cursor.fetchall()
        
        cursor.close()
        db.close()
        return render_template('create_bill.html', user=user,hotel=hotel,bill_no=next_bill_no)
    except Exception as e:
        print(f"Error in create_bill: {e}")
        # Default to 1 if error
        return render_template('create_bill.html', bill_no=1)

@bp.route('/add_item/<int:id>/<int:hotel_id>/<int:bill_no>', methods=['GET', 'POST'])
def add_item(id,hotel_id,bill_no):

    if request.method=='POST':
        veg_name=request.form['veg_name']
        try:
            quantity=float(request.form['quantity'])
            db=get_db_connection()
            cursor=db.cursor(dictionary=True)

            query="select * from registration where id=%s"
            cursor.execute(query,(id,))
            user=cursor.fetchone()

            q="select * from hotel where id=%s"
            cursor.execute(q,(hotel_id,))
            hotel=cursor.fetchone()
            

            inventory_query="select * from inventory_item where item_name=%s"
            cursor.execute(inventory_query,(veg_name,))
            inventory=cursor.fetchone()

            if not inventory:
                flash(f'Item {veg_name} not found in inventory!', 'danger')
                return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id, bill_no=bill_no))
            
            # Stock Validation
            inventory_qty = float(inventory['quantity'])
            if inventory_qty < quantity:
                flash(f'Less stock available for {veg_name}. Only {inventory_qty} {inventory["unit"]} available.', 'danger')
                return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id, bill_no=bill_no))

            rate=float(inventory['price'])
            item_query="insert into item_bill(veg_name,quantity,rate,price,bill_no,hotel_id) values(%s,%s,%s,%s,%s,%s)"
            cursor.execute(item_query,(veg_name,quantity,rate,rate* quantity,bill_no,hotel_id))
            
            # Reduce quantity from inventory
            update_inv_query = "UPDATE inventory_item SET quantity = quantity - %s WHERE item_name = %s"
            cursor.execute(update_inv_query, (quantity, veg_name))
            
            db.commit()

            item_query_list="select * from item_bill where bill_no=%s"
            cursor.execute(item_query_list,(bill_no,))
            items=cursor.fetchall()
            cursor.close()
            db.close()
            return render_template('add_item.html',user=user,hotel=hotel,items=items,bill_no=bill_no)
        except Exception as e:
            print(f"Error in add_item: {e}")
            flash(f"Error adding item: {e}", "danger")
            return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id, bill_no=bill_no))
    else:
        try:
            db=get_db_connection()
            cursor=db.cursor(dictionary=True)

            query="select * from registration where id=%s"
            cursor.execute(query,(id,))
            user=cursor.fetchone()

            
            q="select * from hotel where id=%s"
            cursor.execute(q,(hotel_id,))
            hotel=cursor.fetchone()

            item_query_list="select * from item_bill where bill_no=%s"
            cursor.execute(item_query_list,(bill_no,))
            items=cursor.fetchall()

            cursor.close()
            db.close()
            return render_template('add_item.html',user=user,hotel=hotel,items=items,bill_no=bill_no)
        except Exception as e:
            print(f"Error in add_item: {e}")
            flash(f"Error loading Add Item page: {e}", "danger")
            return redirect(url_for('main.create_bill', id=id))

@bp.route('/delete_item/<int:id>/<int:hotel_id>/<int:item_id>')
def delete_item(id, hotel_id, item_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # 1. Fetch item details to restore inventory
        get_item_query = "SELECT veg_name, quantity FROM item_bill WHERE item_id = %s"
        cursor.execute(get_item_query, (item_id,))
        item_to_restore = cursor.fetchone()
        
        if item_to_restore:
            # 2. Restore inventory
            restore_query = "UPDATE inventory_item SET quantity = quantity + %s WHERE item_name = %s"
            cursor.execute(restore_query, (item_to_restore['quantity'], item_to_restore['veg_name']))
            
            # 3. Delete item
            query = "DELETE FROM item_bill WHERE item_id = %s"
            cursor.execute(query, (item_id,))
            db.commit()
            flash('Item deleted and stock restored successfully!', 'success')
        
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Error in delete_item: {e}")
        flash('Failed to delete item.', 'danger')
    return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id))

@bp.route('/cancel_bill/<int:id>/<int:hotel_id>/<int:bill_no>')
def cancel_bill(id, hotel_id, bill_no):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True) # Use dictionary cursor for easier access
        
        # 1. Fetch items to restore inventory
        get_items_query = "SELECT veg_name, quantity FROM item_bill WHERE bill_no = %s"
        cursor.execute(get_items_query, (bill_no,))
        items_to_restore = cursor.fetchall()
        
        # 2. Restore inventory for each item
        restore_query = "UPDATE inventory_item SET quantity = quantity + %s WHERE item_name = %s"
        for item in items_to_restore:
            cursor.execute(restore_query, (item['quantity'], item['veg_name']))
            
        # 3. Delete items
        delete_query = "DELETE FROM item_bill WHERE bill_no = %s"
        cursor.execute(delete_query, (bill_no,))
        
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('main.create_bill', id=id))
    except Exception as e:
        print(f"Error in cancel_bill: {e}")
        flash('Failed to cancel bill.', 'danger')
        return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id))

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
