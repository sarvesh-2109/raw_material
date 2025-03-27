from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.models import db
from app.routes import init_routes
from app.forms import MaterialEntryForm
import os
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)
    load_dotenv()  
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') 
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Initialize routes
    init_routes(app)
    
    return app