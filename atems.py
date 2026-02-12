from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, login_manager, admin, migrate, init_app
from models.user import User
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)

    # Configure logging: console + file for error review
    log_level = logging.DEBUG if os.getenv("DEBUG", "False").lower() == "true" else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=log_level, format=log_format)
    logger = logging.getLogger(__name__)
    try:
        log_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(log_dir, "atems.log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(fh)
    except Exception as _e:
        import sys
        logging.getLogger(__name__).warning("Could not add atems.log file handler: %s", _e)
        print(f"Could not add atems.log handler: {_e}", file=sys.stderr)
    
    try:
        # Set the database URI from environment variable
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
        if not app.config["SQLALCHEMY_DATABASE_URI"]:
            raise ValueError("No SQLALCHEMY_DATABASE_URI set in environment variables.")
    except Exception as e:
        logger.error(f"Error setting database URI: {e}")
        raise

    # Set the secret key from environment variable
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    if not app.config["SECRET_KEY"]:
        raise ValueError("No SECRET_KEY set in environment variables.")
    
    # Set the debug mode from environment variable
    app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() == "true"

    # When deployed under subpath (e.g. ), set SCRIPT_NAME so url_for generates correct links
    app_root = (os.getenv("APPLICATION_ROOT", "") or "").strip().rstrip("/")
    if app_root and app_root != "/":
        app.config["APPLICATION_ROOT"] = app_root

        class ScriptNameMiddleware:
            def __init__(self, app, script_name):
                self.app = app
                self.script_name = script_name

            def __call__(self, environ, start_response):
                environ["SCRIPT_NAME"] = self.script_name
                return self.app(environ, start_response)

        app.wsgi_app = ScriptNameMiddleware(app.wsgi_app, app_root)

    # Trust X-Forwarded-* headers when behind nginx (fixes https URLs, correct Host)
    if not app.config["DEBUG"] or os.getenv("USE_PROXY_FIX", "").lower() == "true":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Request timing: log [PERF] timestamp method path duration_ms (set ATEMS_PERF_LOG_THRESHOLD_MS=0 to log all)
    try:
        from utils.performance import get_request_timing_middleware
        app.wsgi_app = get_request_timing_middleware(app.wsgi_app)
    except Exception as e:
        logger.warning("Request timing middleware not installed: %s", e)

    # Initialize extensions (init_app does db, login_manager, admin, migrate)
    init_app(app)

    # Ensure all tables exist (fixes "no such table" when using a new or different database)
    with app.app_context():
        from models import Tools, CheckoutHistory  # ensure all models registered for create_all
        db.create_all()
        # If no users exist, create default admin so you can log in (same env pattern as other bots)
        if User.query.count() == 0:
            admin_username = os.getenv("ADMIN_USERNAME", "admin")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            admin_user = User(
                first_name="System",
                last_name="Administrator",
                username=admin_username,
                email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
                badge_id="ADMIN001",
                phone="5550000000",
                department="ATEMS",
                role="admin",
                supervisor_username=admin_username,
                supervisor_email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
                supervisor_phone="5550000000",
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Created default admin user from ADMIN_USERNAME/ADMIN_PASSWORD. Change password after first login.")
    logger.info("Application initialized successfully.")

    # Register blueprints
    from routes import bp
    app.register_blueprint(bp)

    # Run startup self-tests (log to atems.log for error review)
    try:
        from selftest.startup import run_startup_selftests
        run_startup_selftests(app=app, logger=logger)
    except Exception as e:
        logger.warning(f"[SELFTEST] Startup self-tests failed: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"])
