from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, AnonymousUserMixin
from flask_admin import Admin
from flask_migrate import Migrate
from flask_admin.contrib.sqla import ModelView
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
admin = Admin()
migrate = Migrate()

# Custom anonymous user class
class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Anonymous'

# Function to initialize all extensions
def init_app(app):
    try:
        # Configure SQLAlchemy
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///atems.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Connection pool settings - optimized for PostgreSQL
        # For SQLite, use lower settings to avoid "database is locked"
        if 'postgresql' in db_uri:
            # PostgreSQL: Use QueuePool with higher limits
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': 10,
                'pool_timeout': 30,
                'pool_recycle': 1800,
                'max_overflow': 20,
                'pool_pre_ping': True,  # Test connections before use
            }
        elif 'sqlite' in db_uri:
            # SQLite: Use StaticPool or minimal pool to avoid locking
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': 1,
                'pool_timeout': 10,
                'pool_recycle': 3600,
                'connect_args': {'check_same_thread': False},
            }
        else:
            # MySQL or other databases: Use moderate settings
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': 5,
                'pool_timeout': 20,
                'pool_recycle': 1800,
                'pool_pre_ping': True,
            }
        
        db.init_app(app)
        
        # Initialize other extensions
        login_manager.init_app(app)
        admin.init_app(app)
        migrate.init_app(app, db)
        
        # Set the anonymous user
        login_manager.anonymous_user = Anonymous
        
        # Configure LoginManager
        login_manager.login_view = "main.login"
        login_manager.login_message = 'Please log in to access this page.'
        login_manager.login_message_category = 'info'
        
        # Customize Flask-Admin
        admin.name = 'ATEMS Admin'
        admin.template_mode = 'bootstrap4'
        
        # Model views are registered in models/*.py
    except Exception as e:
        print(f"Error initializing extensions: {e}")
        raise
