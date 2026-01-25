import mysql.connector
from app.routes import get_db_connection
from app import create_app

app = create_app()

with app.app_context():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DESCRIBE item_bill")
        columns = cursor.fetchall()
        print("Columns in item_bill table:")
        for col in columns:
            print(col)
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Error inspecting DB: {e}")
