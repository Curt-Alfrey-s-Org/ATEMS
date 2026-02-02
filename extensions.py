from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, AnonymousUserMixin
from flask_admin import Admin
from flask_migrate import Migrate
from flask_admin.contrib.sqla import ModelView

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
admin = Admin()
migrate = Migrate()

# Custom anonymous user class
class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Guest'

# Function to initialize all extensions
def init_app(app):
    try:
        # Configure SQLAlchemy
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///atems.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_POOL_SIZE'] = 10
        app.config['SQLALCHEMY_POOL_TIMEOUT'] = 10
        app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
        
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
