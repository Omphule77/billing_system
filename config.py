import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    # SQLAlchemy (if using)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:Omphule13@localhost/billing_system'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MySQL Configuration (for Flask-MySQL or direct use)
    MYSQL_HOST = os.environ.get('DB_HOST', 'localhost')
    MYSQL_USER = os.environ.get('DB_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('DB_PASSWORD', 'Omphule13@')
    MYSQL_DB = os.environ.get('DB_NAME', 'billing_system')
    MYSQL_PORT = int(os.environ.get('DB_PORT', 3306))