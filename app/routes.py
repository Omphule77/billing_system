from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from app.utils import generate_pdf
from app.drive_utils import upload_to_drive
import datetime

bp = Blueprint('main', __name__)

def get_db():
    client = MongoClient(current_app.config['MONGO_URI'])
    return client['billing_system']

def serialize_doc(doc):
    if doc and '_id' in doc:
        doc['id'] = str(doc['_id'])
    return doc

@bp.route('/hotel_portfolio/<string:id>')
def hotel_portfolio(id):
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
        hotels = [serialize_doc(h) for h in db.hotel.find()]
        return render_template('hotel_portfolio.html', user=user, hotels=hotels)
    except Exception as e:
        print(f"Error in hotel_portfolio: {e}")
        return render_template('hotel_portfolio.html')

@bp.route('/hotel_details/<string:id>/<string:hotel_id>')
def hotel_details(id, hotel_id):
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
        hotel = serialize_doc(db.hotel.find_one({'_id': ObjectId(hotel_id)}))

        pipeline = [
            {'$match': {'hotel_id': hotel_id}},
            {'$group': {'_id': '$veg_name', 'total_qty': {'$sum': '$quantity'}}}
        ]
        chart_results = list(db.item_bill.aggregate(pipeline))
        chart_labels = [row['_id'] for row in chart_results]
        chart_values = [float(row['total_qty']) for row in chart_results]

        bills_pipeline = [
            {'$match': {'hotel_id': hotel_id}},
            {'$group': {'_id': '$bill_no', 'total_items': {'$sum': 1}, 'total_amount': {'$sum': '$price'}}},
            {'$sort': {'_id': -1}}
        ]
        bills_results = list(db.item_bill.aggregate(bills_pipeline))
        bills = [{'bill_no': r['_id'], 'total_items': r['total_items'], 'total_amount': r['total_amount']} for r in bills_results]

        return render_template('hotel_details.html', user=user, hotel=hotel, chart_labels=chart_labels, chart_values=chart_values, bills=bills)
    except Exception as e:
        print(f"Error in hotel_details: {e}")
        return redirect(url_for('main.hotel_portfolio', id=id))

@bp.route('/')
def index():
    return redirect(url_for('main.login'))

@bp.route('/dashboard/<string:id>')
def dashboard(id):
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
        return render_template('dashboard.html', user=user)
    except Exception as e:
        print(f"Error found: {e}")
        return render_template('dashboard.html')

@bp.route('/inventory/<string:id>')
def inventory(id):
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))

        query = {}
        search = request.args.get('search')
        if search:
            query['item_name'] = {'$regex': search, '$options': 'i'}

        category = request.args.get('category')
        if category:
            query['category'] = category

        status = request.args.get('status')
        if status:
            if status == 'Out of Stock':
                query['quantity'] = {'$lte': 0}
            elif status == 'Low Stock':
                query['quantity'] = {'$gt': 0, '$lte': 30}
            elif status == 'In Stock':
                query['quantity'] = {'$gt': 30}

        items = [serialize_doc(i) for i in db.inventory_item.find(query)]
        for item in items:
            item['item_id'] = item['id'] 
        return render_template('inventory.html', user=user, items=items)
    except Exception as e:
        print(f"Error found: {e}")
        return render_template('inventory.html')

@bp.route('/add_inventory_item/<string:id>', methods=['GET', 'POST'])
def add_inventory_item(id):
    if request.method == 'POST':
        try:
            db = get_db()
            user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
            
            item = {
                'item_name': request.form['item_name'],
                'category': request.form['category'],
                'price': float(request.form['price']),
                'unit': request.form['unit'],
                'quantity': float(request.form['quantity']),
                'status': request.form['status']
            }
            db.inventory_item.insert_one(item)
            flash('Inventory item added successfully!', 'success')
            return redirect(url_for('main.inventory', id=id))
        except Exception as e:
            print(f"Error found: {e}")
            flash('Failed to add inventory item!', 'danger')
            return redirect(url_for('main.inventory', id=id))
    else:
        try:
            db = get_db()
            user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
            return render_template('add_inventory_item.html', user=user)
        except Exception as e:
            print(f"Error found: {e}")
            return redirect(url_for('main.inventory', id=id))

@bp.route('/update_inventory_item/<string:item_id>', methods=['POST'])
def update_inventory_item(item_id):
    try:
        data = request.get_json()
        price = float(data.get('price'))
        quantity = float(data.get('quantity'))
        status = data.get('status')

        db = get_db()
        db.inventory_item.update_one({'_id': ObjectId(item_id)}, {'$set': {'price': price, 'quantity': quantity, 'status': status}})
        return jsonify({'success': True, 'message': 'Item updated successfully'})
    except Exception as e:
        print(f"Error updating item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/bill/<string:id>/<string:hotel_id>/<string:bill_no>')
def bill(id, hotel_id, bill_no):
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
        hotel = serialize_doc(db.hotel.find_one({'_id': ObjectId(hotel_id)}))
        items = [serialize_doc(i) for i in db.item_bill.find({'bill_no': bill_no})]

        return render_template('bill.html', user=user, hotel=hotel, items=items, bill_no=bill_no)
    except Exception as e:
        print(f"Error in bill generation: {e}")
        return redirect(url_for('main.create_bill', id=id))

@bp.route('/create_bill/<string:id>')
def create_bill(id):
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
        
        next_bill_no = str(ObjectId())

        query = {}
        search = request.args.get('search')
        if search:
            query['hotel_name'] = {'$regex': search, '$options': 'i'}
            
        hotel = [serialize_doc(h) for h in db.hotel.find(query)]
        return render_template('create_bill.html', user=user, hotel=hotel, bill_no=next_bill_no)
    except Exception as e:
        print(f"Error in create_bill: {e}")
        return render_template('create_bill.html', bill_no=str(ObjectId()))

@bp.route('/add_item/<string:id>/<string:hotel_id>/<string:bill_no>', methods=['GET', 'POST'])
def add_item(id, hotel_id, bill_no):
    if request.method == 'POST':
        veg_name = request.form['veg_name']
        try:
            quantity = float(request.form['quantity'])
            db = get_db()
            user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
            hotel = serialize_doc(db.hotel.find_one({'_id': ObjectId(hotel_id)}))

            inventory = db.inventory_item.find_one({'item_name': veg_name})
            if not inventory:
                flash(f'Item {veg_name} not found in inventory!', 'danger')
                return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id, bill_no=bill_no))
            
            inventory_qty = float(inventory['quantity'])
            if inventory_qty < quantity:
                error_msg = f'Less stock available for {veg_name}. Only {inventory_qty} {inventory["unit"]} available.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                     return jsonify({'success': False, 'message': error_msg})
                flash(error_msg, 'danger')
                return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id, bill_no=bill_no))

            rate = float(inventory['price'])
            item_doc = {
                'veg_name': veg_name,
                'quantity': quantity,
                'rate': rate,
                'price': rate * quantity,
                'bill_no': bill_no,
                'hotel_id': hotel_id,
                'date': datetime.datetime.now()
            }
            res = db.item_bill.insert_one(item_doc)
            new_item_id = str(res.inserted_id)
            
            db.inventory_item.update_one({'item_name': veg_name}, {'$inc': {'quantity': -quantity}})

            pipeline = [{'$match': {'bill_no': bill_no}}, {'$group': {'_id': None, 'total': {'$sum': '$price'}}}]
            total_result = list(db.item_bill.aggregate(pipeline))
            new_total = total_result[0]['total'] if total_result else 0

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                new_item = {
                    'item_id': new_item_id,
                    'veg_name': veg_name,
                    'quantity': quantity,
                    'rate': rate,
                    'price': rate * quantity
                }
                return jsonify({'success': True, 'item': new_item, 'total': new_total, 'message': 'Item added successfully!'})

            items = [serialize_doc(i) for i in db.item_bill.find({'bill_no': bill_no})]
            for i in items: i['item_id'] = i['id']
            return render_template('add_item.html', user=user, hotel=hotel, items=items, bill_no=bill_no)
        except Exception as e:
            print(f"Error in add_item: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)})
            flash(f"Error adding item: {e}", "danger")
            return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id, bill_no=bill_no))
    else:
        try:
            db = get_db()
            user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
            hotel = serialize_doc(db.hotel.find_one({'_id': ObjectId(hotel_id)}))
            items = [serialize_doc(i) for i in db.item_bill.find({'bill_no': bill_no})]
            for i in items: i['item_id'] = i['id']
            return render_template('add_item.html', user=user, hotel=hotel, items=items, bill_no=bill_no)
        except Exception as e:
            print(f"Error in add_item: {e}")
            flash(f"Error loading Add Item page: {e}", "danger")
            return redirect(url_for('main.create_bill', id=id))

@bp.route('/delete_item/<string:id>/<string:hotel_id>/<string:item_id>')
def delete_item(id, hotel_id, item_id):
    try:
        db = get_db()
        item_to_restore = db.item_bill.find_one({'_id': ObjectId(item_id)})
        
        if item_to_restore:
            db.inventory_item.update_one(
                {'item_name': item_to_restore['veg_name']},
                {'$inc': {'quantity': item_to_restore['quantity']}}
            )
            db.item_bill.delete_one({'_id': ObjectId(item_id)})
            flash('Item deleted and stock restored successfully!', 'success')
        
    except Exception as e:
        print(f"Error in delete_item: {e}")
        flash('Failed to delete item.', 'danger')
    return redirect(url_for('main.add_item', id=id, hotel_id=hotel_id))

@bp.route('/cancel_bill/<string:id>/<string:hotel_id>/<string:bill_no>')
def cancel_bill(id, hotel_id, bill_no):
    try:
        db = get_db()
        items_to_restore = db.item_bill.find({'bill_no': bill_no})
        
        for item in items_to_restore:
            db.inventory_item.update_one(
                {'item_name': item['veg_name']},
                {'$inc': {'quantity': item['quantity']}}
            )
            
        db.item_bill.delete_many({'bill_no': bill_no})
        return redirect(url_for('main.create_bill', id=id))
    except Exception as e:
        print(f"Error in cancel_bill: {e}")
        flash(f"Error cancelling bill: {e}", "danger")
        return redirect(url_for('main.create_bill', id=id))

@bp.route('/sales/<string:id>')
def sales(id):
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
        
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

        item_pipeline = [
            {'$match': {'$expr': {'$and': [{'$eq': [{'$month': '$date'}, selected_month]}, {'$eq': [{'$year': '$date'}, selected_year]}]}}},
            {'$group': {'_id': '$veg_name', 'total_qty': {'$sum': '$quantity'}}}
        ]
        item_results = list(db.item_bill.aggregate(item_pipeline))
        item_labels = [row['_id'] for row in item_results]
        item_values = [float(row['total_qty']) for row in item_results]

        revenue_pipeline = [
            {'$match': {'$expr': {'$eq': [{'$year': '$date'}, revenue_year]}}},
            {'$group': {
                '_id': {'$month': '$date'}, 
                'total_revenue': {'$sum': '$price'}
            }},
            {'$sort': {'_id': 1}}
        ]
        revenue_results = list(db.item_bill.aggregate(revenue_pipeline))
        
        import calendar
        month_labels = [calendar.month_name[row['_id']] for row in revenue_results]
        month_values = [float(row['total_revenue']) for row in revenue_results]

        hotel_pipeline = [
            {'$match': {'$expr': {'$and': [{'$eq': [{'$month': '$date'}, selected_month]}, {'$eq': [{'$year': '$date'}, selected_year]}]}}},
            {'$group': {'_id': '$hotel_id', 'total_spent': {'$sum': '$price'}}},
            {'$sort': {'total_spent': -1}}
        ]
        hotel_results = list(db.item_bill.aggregate(hotel_pipeline))
        
        hotel_labels = []
        hotel_values = []
        for row in hotel_results:
            hotel_doc = db.hotel.find_one({'_id': ObjectId(row['_id'])})
            if hotel_doc:
                hotel_labels.append(hotel_doc['hotel_name'])
                hotel_values.append(float(row['total_spent']))

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

@bp.route('/add_hotel/<string:id>', methods=['GET','POST'])
def add_hotel(id):
    if request.method == 'POST':
        try:
            db = get_db()
            hotel = {
                'owner_name': request.form['owner_name'],
                'mobile': request.form['mobile'],
                'email': request.form['email'],
                'hotel_name': request.form['hotel_name'],
                'address': request.form['address']
            }
            db.hotel.insert_one(hotel)
            flash('Hotel added successfully!', 'success')
            return redirect(url_for('main.create_bill', id=id))
        except Exception as e:
            print(f"Error in add_hotel: {e}")
            flash('Failed to add hotel!', 'danger')
            return redirect(url_for('main.create_bill', id=id))
    else:
        try:
            db = get_db()
            user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
            return render_template('add_hotel.html', user=user)
        except Exception as e:
            print(f"Error in add_hotel: {e}")
            return redirect(url_for('main.create_bill', id=id))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            db = get_db()
            user = serialize_doc(db.registration.find_one({'email': email}))
            
            if user and user['password'] == password:
                session['user_id'] = user['id']
                flash('Login successful!', 'success')
                return redirect(url_for('main.sales', id=user['id']))
            else:
                 flash('Invalid email or password', 'danger')
                
        except Exception as e:
            print(f"DEBUG: Error during login: {e}")
            flash(f'An error occurred: {e}', 'danger')

    return render_template('login.html')

@bp.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        try:
            db = get_db()
            new_user = {
                'name': request.form['name'],
                'mobile': request.form['mobile'],
                'email': request.form['email'],
                'address': request.form['address'],
                'password': request.form['password']
            }
            res = db.registration.insert_one(new_user)
            print(f"DEBUG: Commit successful. Row ID: {res.inserted_id}")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            print(f"DEBUG: Error during registration: {e}")
            flash(f'An error occurred: {e}', 'danger')
            return render_template('registration.html')
    return render_template('registration.html')

@bp.route('/search_items')
def search_items():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify([])
        
        db = get_db()
        items = list(db.inventory_item.find({'item_name': {'$regex': query, '$options': 'i'}}).limit(10))
        for item in items:
            item['_id'] = str(item['_id'])
            
        return jsonify(items)
    except Exception as e:
        print(f"Error in search_items: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/send_bill_whatsapp/<string:id>/<string:hotel_id>/<string:bill_no>', methods=['POST'])
def send_bill_whatsapp(id, hotel_id, bill_no):
    from app.whatsapp_utils import send_whatsapp_message
    print(f"\n\n!!! USER REQUEST START: ID={id}, Hotel={hotel_id}, Bill={bill_no} !!!")
    try:
        db = get_db()
        user = serialize_doc(db.registration.find_one({'_id': ObjectId(id)}))
        hotel = serialize_doc(db.hotel.find_one({'_id': ObjectId(hotel_id)}))

        if not user or not hotel:
             return jsonify({'success': False, 'message': 'User or Hotel not found.'}), 404

        items = [serialize_doc(i) for i in db.item_bill.find({'bill_no': bill_no})]

        html = render_template('pdf_bill.html', user=user, hotel=hotel, items=items, bill_no=bill_no, date=datetime.datetime.now().strftime("%d-%m-%Y"))
        
        pdf_filename = f"bill_{bill_no}_{hotel_id}.pdf"
        static_bills_dir = os.path.join(current_app.root_path, 'static', 'bills')
        if not os.path.exists(static_bills_dir):
            os.makedirs(static_bills_dir)
            
        pdf_path = os.path.join(static_bills_dir, pdf_filename)
        print(f"Using static PDF path: {pdf_path}")
        
        success = generate_pdf(html, pdf_path)
        
        file_size = 0
        if success and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
        
        if file_size < 100:
             simple_html = "<html><body><h1>FALLBACK BILL</h1><p>The original bill generation failed.</p></body></html>"
             generate_pdf(simple_html, pdf_path)
        
        if os.path.exists(pdf_path):
             try:
                 pdf_link = upload_to_drive(pdf_path, pdf_filename)
             except Exception as e:
                 print(f"Drive Upload Failed: {e}")
                 pdf_link = f"FAILED_UPLOAD_LOCAL_PATH: {pdf_path}"

             mobile = hotel['mobile']
             import re
             clean_mobile = re.sub(r'\D', '', str(mobile))
             if len(clean_mobile) == 10:
                 clean_mobile = '91' + clean_mobile
             
             total = sum([float(item.get('price', 0)) for item in items])
             msg = f"Hello {hotel['hotel_name']}, please find the generated bill #{bill_no} here: {pdf_link} . Total Amount: Rs. {total}."
             
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