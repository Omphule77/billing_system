import mysql.connector
from app.routes import get_db_connection
from app import create_app

app = create_app()

with app.app_context():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Check if column exists first (naive way, or just try add and catch error)
        try:
            print("Attempting to add hotel_id column...")
            cursor.execute("ALTER TABLE item_bill ADD COLUMN hotel_id INT")
            db.commit()
            print("Successfully added hotel_id column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("Column hotel_id already exists.")
            else:
                print(f"Error adding column: {e}")

        # describe again to verify
        cursor.execute("DESCRIBE item_bill")
        columns = cursor.fetchall()
        print("Current columns in item_bill:")
        for col in columns:
            print(col)

        cursor.close()
        db.close()
    except Exception as e:
        print(f"Error connecting to DB: {e}")
