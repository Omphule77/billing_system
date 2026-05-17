import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # -----------------------------
    # DATABASE CONFIGURATION
    # -----------------------------

    # MongoDB connection URI (use local if not specified)
    MONGO_URI = os.environ.get("mongodb+srv://omphule77_db_user:<db_password>@cluster0.xwlfth2.mongodb.net/", "mongodb+srv://omphule77_db_user:Omphule77@cluster0.xwlfth2.mongodb.net/")