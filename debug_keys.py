import mysql.connector
from app.routes import get_db_connection
from app import create_app

app = create_app()

with app.app_context():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        print("Checking Item Bill columns...")
        bill_no = 1
        item_query_list="select * from item_bill where bill_no=%s"
        cursor.execute(item_query_list,(bill_no,))
        items=cursor.fetchall()
        
        if items:
            print(f"First item keys: {list(items[0].keys())}")
        else:
            print("No items found in bill 1.")
            
            # Insert a dummy item to check keys
            print("Inserting dummy item...")
            cursor.execute("INSERT INTO item_bill (veg_name, quantity, rate, price, bill_no, hotel_id) VALUES ('Debug', 1, 10, 10, 1, 1)")
            db.commit()
            
            cursor.execute("select * from item_bill where bill_no=1")
            items = cursor.fetchall()
            print(f"First item keys (after insert): {list(items[0].keys())}")
            
            # Clean up
            # cursor.execute("DELETE FROM item_bill WHERE veg_name='Debug'")
            # db.commit()

        cursor.close()
        db.close()
    except Exception as e:
        print(f"Caught exception: {e}")
