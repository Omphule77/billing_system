from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
import mysql.connector
import os
from app.utils import generate_pdf

from app.drive_utils import upload_to_drive

bp = Blueprint('main', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host=current_app.config['MYSQL_HOST'],
        user=current_app.config['MYSQL_USER'],
        password=current_app.config['MYSQL_PASSWORD'],
        database=current_app.config['MYSQL_DB']
    )



@bp.route('/hotel_portfolio/<int:id>')
def hotel_portfolio(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query="select * from registration where id=%s"
        cursor.execute(query,(id,))
        user=cursor.fetchone()
        
        q="select * from hotel"
        cursor.execute(q)
        hotels=cursor.fetchall()
        
        cursor.close()
        db.close()
        return render_template('hotel_portfolio.html', user=user, hotels=hotels)
    except Exception as e:
        print(f"Error in hotel_portfolio: {e}")
        return render_template('hotel_portfolio.html')

@bp.route('/hotel_details/<int:id>/<int:hotel_id>')
def hotel_details(id, hotel_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get User
        query="select * from registration where id=%s"
        cursor.execute(query,(id,))
        user=cursor.fetchone()
        
        # Get Hotel Details
        q="select * from hotel where id=%s"
        cursor.execute(q, (hotel_id,))
        hotel=cursor.fetchone()

        # Get Item Analysis for Pie Chart (Sum quantity grouped by veg_name)
        chart_query = """
            SELECT veg_name, SUM(quantity) as total_qty 
            FROM item_bill 
            WHERE hotel_id = %s 
            GROUP BY veg_name
        """
        cursor.execute(chart_query, (hotel_id,))
        chart_results = cursor.fetchall()
        
        chart_labels = [row['veg_name'] for row in chart_results]
        chart_values = [float(row['total_qty']) for row in chart_results]

        # Get All Bills Summary
        # Since we don't have a bills table, we group item_bill by bill_no
        bills_query = """
            SELECT bill_no, count(*) as total_items, SUM(price) as total_amount 
            FROM item_bill 
            WHERE hotel_id = %s 
            GROUP BY bill_no 
            ORDER BY bill_no DESC
        """
        cursor.execute(bills_query, (hotel_id,))
        bills = cursor.fetchall()

        cursor.close()
        db.close()
        
        return render_template('hotel_details.html', 
                             user=user, 
                             hotel=hotel, 
                             chart_labels=chart_labels, 
                             chart_values=chart_values,
                             bills=bills)
    except Exception as e:
        print(f"Error in hotel_details: {e}")
        return redirect(url_for('main.hotel_portfolio', id=id))

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

        # Base query
        q = "select * from inventory_item WHERE 1=1"
        params = []

        # Filter by Search (Item Name)
        search = request.args.get('search')
        if search:
            q += " AND item_name LIKE %s"
            params.append(f"%{search}%")

        # Filter by Category
        category = request.args.get('category')
        if category:
            q += " AND category = %s"
            params.append(category)

        # Filter by Status (Using Quantity logic)
        status = request.args.get('status')
        if status:
            if status == 'Out of Stock':
                q += " AND quantity <= 0"
            elif status == 'Low Stock':
                q += " AND quantity > 0 AND quantity <= 30"
            elif status == 'In Stock':
                q += " AND quantity > 30"

        cursor.execute(q, tuple(params))
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
                error_msg = f'Less stock available for {veg_name}. Only {inventory_qty} {inventory["unit"]} available.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                     cursor.close()
                     db.close()
                     return jsonify({'success': False, 'message': error_msg})
                flash(error_msg, 'danger')
                return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id, bill_no=bill_no))

            rate=float(inventory['price'])
            item_query="insert into item_bill(veg_name,quantity,rate,price,bill_no,hotel_id,date) values(%s,%s,%s,%s,%s,%s,NOW())"
            cursor.execute(item_query,(veg_name,quantity,rate,rate* quantity,bill_no,hotel_id))
            new_item_id = cursor.lastrowid
            
            # Reduce quantity from inventory
            update_inv_query = "UPDATE inventory_item SET quantity = quantity - %s WHERE item_name = %s"
            cursor.execute(update_inv_query, (quantity, veg_name))
            
            db.commit()

            # Calculate new total
            total_query = "SELECT SUM(price) as total FROM item_bill WHERE bill_no=%s"
            cursor.execute(total_query, (bill_no,))
            total_result = cursor.fetchone()
            new_total = total_result['total'] if total_result['total'] else 0

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                new_item = {
                    'item_id': new_item_id,
                    'veg_name': veg_name,
                    'quantity': quantity,
                    'rate': rate,
                    'price': rate * quantity
                }
                cursor.close()
                db.close()
                return jsonify({'success': True, 'item': new_item, 'total': new_total, 'message': 'Item added successfully!'})

            item_query_list="select * from item_bill where bill_no=%s"
            cursor.execute(item_query_list,(bill_no,))
            items=cursor.fetchall()
            cursor.close()
            db.close()
            return render_template('add_item.html',user=user,hotel=hotel,items=items,bill_no=bill_no)
        except Exception as e:
            print(f"Error in add_item: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)})
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
        flash(f"Error cancelling bill: {e}", "danger")
        return redirect(url_for('main.create_bill', id=id))

@bp.route('/sales/<int:id>')
def sales(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Get User
        query="select * from registration where id=%s"
        cursor.execute(query,(id,))
        user=cursor.fetchone()

        # Get Date Filter Parameters
        import datetime
        current_date = datetime.datetime.now()
        
        try:
            selected_month = int(request.args.get('month', current_date.month))
            selected_year = int(request.args.get('year', current_date.year))
        except ValueError:
            selected_month = current_date.month
            selected_year = current_date.year

        try:
            revenue_year = int(request.args.get('revenue_year', selected_year))
        except ValueError:
            revenue_year = selected_year

        # 1. Item Quantity This Month (Pie Chart)
        item_query = """
            SELECT veg_name, SUM(quantity) as total_qty 
            FROM item_bill 
            WHERE MONTH(date) = %s AND YEAR(date) = %s
            GROUP BY veg_name
        """
        cursor.execute(item_query, (selected_month, selected_year))
        item_results = cursor.fetchall()
        item_labels = [row['veg_name'] for row in item_results]
        item_values = [float(row['total_qty']) for row in item_results]

        # 2. Monthly Revenue This Year (Histogram/Bar) - Keep this for the whole year context, or filter? 
        # Requirement says "choose which month and year i want to see the data". 
        # For monthly revenue comparison, usually showing the whole year of the SELECTED year is better.
        revenue_query = """
            SELECT MONTHNAME(date) as month, SUM(price) as total_revenue
            FROM item_bill
            WHERE YEAR(date) = %s
            GROUP BY MONTH(date), MONTHNAME(date)
            ORDER BY MONTH(date)
        """
        cursor.execute(revenue_query, (revenue_year,))
        revenue_results = cursor.fetchall()
        month_labels = [row['month'] for row in revenue_results]
        month_values = [float(row['total_revenue']) for row in revenue_results]

        # 3. Hotel Spending This Month (Graph)
        hotel_query = """
            SELECT h.hotel_name, SUM(ib.price) as total_spent
            FROM item_bill ib
            JOIN hotel h ON ib.hotel_id = h.id
            WHERE MONTH(ib.date) = %s AND YEAR(ib.date) = %s
            GROUP BY h.id, h.hotel_name
            ORDER BY total_spent DESC
        """
        cursor.execute(hotel_query, (selected_month, selected_year))
        hotel_results = cursor.fetchall()
        hotel_labels = [row['hotel_name'] for row in hotel_results]
        hotel_values = [float(row['total_spent']) for row in hotel_results]

        cursor.close()
        db.close()

        # Format display string
        # datetime module is already imported inside function scope in original code, but let's use the one we imported above
        display_date = datetime.date(selected_year, selected_month, 1)
        year_month = display_date.strftime("%B %Y")

        return render_template('sales.html', 
                             user=user,
                             item_labels=item_labels, item_values=item_values,
                             month_labels=month_labels, month_values=month_values,
                             hotel_labels=hotel_labels, hotel_values=hotel_values,
                             year_month=year_month,
                             selected_month=selected_month,
                             selected_year=selected_year,
                             revenue_year=revenue_year)

    except Exception as e:
        print(f"Error in sales: {e}")
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
                    session['user_id'] = user['id']
                    flash('Login successful!', 'success')
                    return redirect(url_for('main.sales', id=user['id']))
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

@bp.route('/search_items')
def search_items():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify([])
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Search for items starting with or containing the query string
        sql = "SELECT item_name, price, unit, quantity FROM inventory_item WHERE item_name LIKE %s LIMIT 10"
        cursor.execute(sql, (f"%{query}%",))
        items = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return jsonify(items)
    except Exception as e:
        print(f"Error in search_items: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/send_bill_whatsapp/<int:id>/<int:hotel_id>/<int:bill_no>', methods=['POST'])
def send_bill_whatsapp(id, hotel_id, bill_no):
    from app.whatsapp_utils import send_whatsapp_message
    print(f"\n\n!!! USER REQUEST START: ID={id}, Hotel={hotel_id}, Bill={bill_no} !!!")
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Get Data for PDF
        # User
        query = "select * from registration where id=%s"
        cursor.execute(query, (id,))
        user = cursor.fetchone()

        # Hotel
        q = "select * from hotel where id=%s"
        cursor.execute(q, (hotel_id,))
        hotel = cursor.fetchone()

        if not user or not hotel:
             cursor.close()
             db.close()
             return jsonify({'success': False, 'message': 'User or Hotel not found.'}), 404

        # Items
        item_query = "select * from item_bill where bill_no=%s"
        cursor.execute(item_query, (bill_no,))
        items = cursor.fetchall()
        
        cursor.close()
        db.close()

        # Render HTML for PDF
        from datetime import datetime
        html = render_template('pdf_bill.html', user=user, hotel=hotel, items=items, bill_no=bill_no, date=datetime.now().strftime("%d-%m-%Y"))
        
        # Determine paths - SAVE TO STATIC FOLDER
        pdf_filename = f"bill_{bill_no}_{hotel_id}.pdf"
        
        # Ensure static/bills exists
        static_bills_dir = os.path.join(current_app.root_path, 'static', 'bills')
        if not os.path.exists(static_bills_dir):
            os.makedirs(static_bills_dir)
            
        pdf_path = os.path.join(static_bills_dir, pdf_filename)
        print(f"Using static PDF path: {pdf_path}")
        
        # Generate PDF
        success = generate_pdf(html, pdf_path)
        
        # Verify file size
        file_size = 0
        if success and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"Generated PDF size: {file_size} bytes")
        
        if file_size < 100:
             print("PDF corrupted or too small. Attempting fallback simple PDF...")
             simple_html = "<html><body><h1>FALLBACK BILL</h1><p>The original bill generation failed.</p></body></html>"
             generate_pdf(simple_html, pdf_path)
             
             print(f"PDF Generated Successfully (Fallback): {pdf_path}")
        
        # PROCEED IF FILE EXISTS (Original or Fallback)
        if os.path.exists(pdf_path):
             # Upload to Google Drive
             try:
                 pdf_link = upload_to_drive(pdf_path, pdf_filename)
                 print(f"Docs Link: {pdf_link}")
             except Exception as e:
                 print(f"Drive Upload Failed: {e}")
                 # Fallback to local (though it won't work on mobile)
                 pdf_link = f"FAILED_UPLOAD_LOCAL_PATH: {pdf_path}"

             # Send via WhatsApp
             mobile = hotel['mobile']
             # Format mobile (India specific 91)
             import re
             clean_mobile = re.sub(r'\D', '', str(mobile))
             if len(clean_mobile) == 10:
                 clean_mobile = '91' + clean_mobile
             
             # Calculate total
             total = sum([float(item['price'] or 0) for item in items])
             
             # Construct Message with Link
             msg = f"Hello {hotel['hotel_name']}, please find the generated bill #{bill_no} here: {pdf_link} . Total Amount: Rs. {total}."
             
             # Send Text Only (File Path = None)
             success, message = send_whatsapp_message(clean_mobile, msg, file_path=None)
             
             if success:
                 return jsonify({'success': True, 'message': 'Bill link sent via WhatsApp successfully!'})
             else:
                  with open("error.log", "a") as f:
                       f.write(f"Whatsapp Failure: {message}\n")
                  return jsonify({'success': False, 'message': f'Failed to send WhatsApp: {message}'})
        else:
             return jsonify({'success': False, 'message': 'Failed to generate PDF (Empty File).'})

    except Exception as e:
        print(f"Error in send_bill_whatsapp: {e}")
        with open("error.log", "a") as f:
             f.write(f"Error: {str(e)}\n")
        return jsonify({'success': False, 'message': str(e)}), 500