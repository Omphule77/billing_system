import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # -----------------------------
    # DATABASE CONFIGURATION
    # -----------------------------

    # If DATABASE_URL exists (Production - AWS)
    # use it directly
    if os.environ.get("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    else:
        # Local development fallback
        MYSQL_HOST = os.environ.get("DB_HOST", "localhost")
        MYSQL_USER = os.environ.get("DB_USER", "root")
        MYSQL_PASSWORD = os.environ.get("DB_PASSWORD", "Omphule13@")
        MYSQL_DB = os.environ.get("DB_NAME", "mysql")
        MYSQL_PORT = os.environ.get("DB_PORT", "3306")

        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional: For direct PyMySQL usage
    MYSQL_HOST = os.environ.get("DB_HOST", "localhost")
    MYSQL_USER = os.environ.get("DB_USER", "root")
    MYSQL_PASSWORD = os.environ.get("DB_PASSWORD", "Omphule13@")
    MYSQL_DB = os.environ.get("DB_NAME", "billing_system")
    MYSQL_PORT = int(os.environ.get("DB_PORT", 3306))