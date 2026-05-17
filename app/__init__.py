from flask import Flask
from config import Config

def create_app(config_class=Config):
    application = Flask(__name__)
    application.config.from_object(config_class)

    from app import routes
    application.register_blueprint(routes.bp)

    return application
