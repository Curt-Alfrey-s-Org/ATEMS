from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, AnonymousUserMixin
from flask_admin import Admin, AdminIndexView, BaseView
from flask_migrate import Migrate
from flask_admin.contrib.sqla import ModelView
import os


# ----------------------------------------------------------------------------
# Flask-Admin access control (security review 2026-09-25, finding #1)
# Every view registered on `admin` (including the /admin index) must use one of
# the Secure* classes below so only logged-in users with role 'admin' get in.
# ----------------------------------------------------------------------------
class AdminAccessMixin:
    """Restrict a Flask-Admin view to authenticated admins."""

    def is_accessible(self):
        from flask_login import current_user
        if not current_user.is_authenticated:
            return False
        is_admin = getattr(current_user, "is_admin", None)
        return bool(callable(is_admin) and is_admin())

    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for, flash
        from flask_login import current_user
        if current_user.is_authenticated:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('main.login'))


class SecureAdminIndexView(AdminAccessMixin, AdminIndexView):
    """Admin landing page (/admin/), admins only."""


class SecureModelView(AdminAccessMixin, ModelView):
    """SQLAlchemy ModelView, admins only."""


class SecureBaseView(AdminAccessMixin, BaseView):
    """Custom Flask-Admin page, admins only."""


# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
admin = Admin(index_view=SecureAdminIndexView())
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
