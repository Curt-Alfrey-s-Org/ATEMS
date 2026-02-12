import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from forms import CheckInOutForm
from models import User, Tools, CheckoutHistory
from extensions import db
from datetime import datetime, time
from sqlalchemy.exc import SQLAlchemyError
from utils.calibration import is_calibration_overdue
import logging
import bcrypt

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT-BASED USER CREDENTIALS (inspired by rankings-bot)
# ============================================================================

# Default credentials (fallback if env vars not set)
_DEFAULT_USERS = {
    "admin": ("admin", "admin123"),
    "user": ("user", "user123"),
}

_ENV_USERS = {}


def _load_env_users():
    """
    Load environment-based credentials from env variables.
    Format: ADMIN_USERNAME/ADMIN_PASSWORD, USER_USERNAME/USER_PASSWORD
    Falls back to defaults if not configured.
    """
    global _ENV_USERS
    _ENV_USERS = _DEFAULT_USERS.copy()  # Start with defaults
    
    # Admin credentials (override default)
    admin_user = os.getenv("ADMIN_USERNAME", "").strip()
    admin_pass = os.getenv("ADMIN_PASSWORD", "").strip()
    if admin_user and admin_pass:
        _ENV_USERS[admin_user] = ("admin", admin_pass)
        logger.info(f"Loaded admin user from env: {admin_user}")
    
    # User credentials (override default)
    user_user = os.getenv("USER_USERNAME", "").strip()
    user_pass = os.getenv("USER_PASSWORD", "").strip()
    if user_user and user_pass:
        _ENV_USERS[user_user] = ("user", user_pass)
        logger.info(f"Loaded user from env: {user_user}")
    
    logger.info(f"Auth system initialized with {len(_ENV_USERS)} environment-based users")


def _check_env_password(username: str, password: str) -> tuple[bool, str]:
    """Check credentials against environment-based users. Returns (success, role)."""
    if not _ENV_USERS:
        _load_env_users()
    
    if username not in _ENV_USERS:
        return False, ""
    
    expected_role, expected_pass = _ENV_USERS[username]
    if expected_pass == password:
        return True, expected_role
    
    return False, ""

@bp.app_context_processor
def inject_datetime():
    return {'datetime': datetime}


@bp.route('/')
def index():
    """Landing page - show splash with login (must sign in) if not logged in, else dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('splash_login.html')


@bp.route('/splash')
def splash():
    """Professional splash screen for demo site."""
    return render_template('splash.html')


@bp.route('/app')
@bp.route('/app/<path:path>')
@login_required
def serve_spa(path=None):
    """Serve React SPA from static/app/ (Phase 7 frontend)."""
    import os
    root = os.path.join(os.path.dirname(__file__), 'static', 'app')
    if path and os.path.exists(os.path.join(root, path)):
        return send_from_directory(root, path)
    return send_from_directory(root, 'index.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with stat cards, category breakdown, usage trend, and recent activity.
    Independent query groups run in parallel when ATEMS_DASHBOARD_PARALLEL=1 (default on).
    """
    from flask import current_app
    from utils.calibration import is_calibration_overdue
    from sqlalchemy import func
    from datetime import timedelta, timezone

    try:
        _now = datetime.now(timezone.utc).replace(tzinfo=None)
        seven_days_ago = _now - timedelta(days=7)
        today_str = _now.strftime('%Y-%m-%d')
        d30 = (_now + timedelta(days=30)).strftime('%Y-%m-%d')
        d60 = (_now + timedelta(days=60)).strftime('%Y-%m-%d')

        use_parallel = os.environ.get("ATEMS_DASHBOARD_PARALLEL", "1").strip().lower() in ("1", "true", "yes")

        if use_parallel:
            app = current_app._get_current_object()

            def block_counts():
                total = Tools.query.count()
                checked_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).count()
                return (total, checked_out)

            def block_cal_tools():
                return Tools.query.filter(
                    Tools.tool_calibration_due != "N/A",
                    Tools.tool_calibration_due.isnot(None),
                ).all()

            def block_recent():
                return CheckoutHistory.query.order_by(CheckoutHistory.event_time.desc()).limit(10).all()

            def block_category_breakdown():
                rows = db.session.query(
                    Tools.category, func.count(Tools.id).label('count')
                ).filter(Tools.category.isnot(None), Tools.category != '').group_by(Tools.category).order_by(func.count(Tools.id).desc()).all()
                return [{'name': c[0], 'count': c[1]} for c in rows]

            def block_usage_trend():
                rows = db.session.query(
                    func.date(CheckoutHistory.event_time).label('day'),
                    func.count(CheckoutHistory.id).label('count')
                ).filter(
                    CheckoutHistory.event_time >= seven_days_ago,
                    CheckoutHistory.action == 'checkout'
                ).group_by(func.date(CheckoutHistory.event_time)).order_by('day').all()
                return [{'day': str(r[0]), 'count': r[1]} for r in rows]

            def block_overdue_returns():
                from utils.performance import get_overdue_returns_bulk
                tools_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).all()
                return get_overdue_returns_bulk(tools_out, _now, Tools, CheckoutHistory)

            from utils.performance import run_in_parallel
            counts, cal_tools, recent, category_breakdown, usage_trend, overdue_returns = run_in_parallel(
                app,
                [block_counts, block_cal_tools, block_recent, block_category_breakdown, block_usage_trend, block_overdue_returns],
            )
            total, checked_out = counts
            in_stock = total - checked_out
        else:
            total = Tools.query.count()
            checked_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).count()
            in_stock = total - checked_out
            cal_tools = Tools.query.filter(
                Tools.tool_calibration_due != "N/A",
                Tools.tool_calibration_due.isnot(None),
            ).all()
            recent = CheckoutHistory.query.order_by(CheckoutHistory.event_time.desc()).limit(10).all()
            category_breakdown = db.session.query(
                Tools.category, func.count(Tools.id).label('count')
            ).filter(Tools.category.isnot(None), Tools.category != '').group_by(Tools.category).order_by(func.count(Tools.id).desc()).all()
            category_breakdown = [{'name': c[0], 'count': c[1]} for c in category_breakdown]
            usage_rows = db.session.query(
                func.date(CheckoutHistory.event_time).label('day'),
                func.count(CheckoutHistory.id).label('count')
            ).filter(
                CheckoutHistory.event_time >= seven_days_ago,
                CheckoutHistory.action == 'checkout'
            ).group_by(func.date(CheckoutHistory.event_time)).order_by('day').all()
            usage_trend = [{'day': str(r[0]), 'count': r[1]} for r in usage_rows]
            tools_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).all()
            from utils.performance import get_overdue_returns_bulk
            overdue_returns = get_overdue_returns_bulk(tools_out, _now, Tools, CheckoutHistory)

        calibration_overdue = sum(1 for t in cal_tools if is_calibration_overdue(t.tool_calibration_due))
        cal_overdue = sum(1 for t in cal_tools if is_calibration_overdue(t.tool_calibration_due))
        cal_due_30 = sum(1 for t in cal_tools if t.tool_calibration_due != 'N/A' and not is_calibration_overdue(t.tool_calibration_due) and today_str <= t.tool_calibration_due <= d30)
        cal_due_60 = sum(1 for t in cal_tools if t.tool_calibration_due != 'N/A' and not is_calibration_overdue(t.tool_calibration_due) and d30 < t.tool_calibration_due <= d60)
        cal_due_90 = sum(1 for t in cal_tools if t.tool_calibration_due != 'N/A' and not is_calibration_overdue(t.tool_calibration_due) and t.tool_calibration_due > d60)
        calibration_summary = [
            {'label': 'Overdue', 'count': cal_overdue, 'color': 'amber'},
            {'label': 'Due in 30 days', 'count': cal_due_30, 'color': 'yellow'},
            {'label': 'Due in 60 days', 'count': cal_due_60, 'color': 'blue'},
            {'label': 'Due in 90+ days', 'count': cal_due_90, 'color': 'emerald'},
        ]
        categories = [c['name'] for c in category_breakdown]
        max_usage = max((u['count'] for u in usage_trend), default=1)

        return render_template(
            "dashboard.html",
            total_tools=total,
            checked_out=checked_out,
            in_stock=in_stock,
            calibration_overdue=calibration_overdue,
            recent_events=recent,
            category_breakdown=category_breakdown,
            usage_trend=usage_trend,
            calibration_summary=calibration_summary,
            categories=categories,
            max_usage=max_usage,
            overdue_returns=overdue_returns,
            overdue_returns_count=len(overdue_returns),
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("Dashboard database error")
        flash("Unable to load dashboard. Please try again.", "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        logger.exception("Dashboard error: %s", e)
        flash("An error occurred loading the dashboard.", "error")
        return redirect(url_for("main.index"))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login endpoint supporting:
    1. Environment-based credentials (admin, user)
    2. Database-backed users with bcrypt password hashing
    
    Pattern inspired by rankings-bot for simplicity and clarity.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        password = request.form.get('password') or ""
        
        # Validation: username required
        if not username:
            flash('Username required.', 'error')
            return render_template('login.html')
        
        # Step 1: Check environment-based credentials (admin/user)
        env_ok, env_role = _check_env_password(username, password)
        if env_ok:
            # Create or get admin user from environment
            user = User.query.filter_by(username=username).first()
            if not user:
                # Create temporary admin user from environment credentials
                logger.info(f"Creating environment-based user: {username} with role {env_role}")
                user = User(
                    username=username,
                    email=f"{username}@local.env",
                    first_name=username.capitalize(),
                    last_name="(env)",
                    badge_id=f"ENV-{username}",
                    phone="0000000000",
                    department="Administration",
                    supervisor_username=username,
                    supervisor_email=f"{username}@local.env",
                    supervisor_phone="0000000000",
                    role=env_role
                )
                user.set_password(password)
                db.session.add(user)
                try:
                    db.session.commit()
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Error creating environment user: {e}")
                    flash('Login system error. Please try again.', 'error')
                    return render_template('login.html')
            
            login_user(user)
            logger.info(f"User '{username}' logged in via environment-based credentials as {env_role}")
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next') or url_for('main.dashboard')
            return redirect(next_page)
        
        # Step 2: Check database-backed users
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            logger.info(f"User '{username}' logged in via database-backed credentials as {user.role}")
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next') or url_for('main.dashboard')
            return redirect(next_page)
        
        # Step 3: Log failed attempt and return error
        logger.warning(f"Failed login attempt for username: {username}")
        flash('Invalid username or password.', 'error')
    
    return render_template('login.html')


@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


def _checkinout_logic(form, json_response=True):
    """Shared logic for form and API check-in/out. Returns (status, message, extra)."""
    user = User.query.filter_by(username=form.username.data).first()
    tool = Tools.query.filter_by(tool_id_number=form.tool_id_number.data).first()

    if not user:
        return "error", f"User '{form.username.data}' not found. Check the username.", None
    if not tool:
        return "error", f"Tool '{form.tool_id_number.data}' not found. Check the tool ID.", None
    if form.badge_id.data != user.badge_id:
        return "error", f"Badge ID does not match user '{user.username}'. Please scan the correct badge.", None

    now = datetime.now()
    extra = {}

    job_id = (form.job_id.data or "").strip() or None
    condition_val = (form.condition.data or "").strip() or None

    if tool.checked_out_by == user.username:
        # Check in
        tool.checked_out_by = None
        tool.checkin_time = now
        hist = CheckoutHistory(
            tool_id_number=tool.tool_id_number,
            tool_name=tool.tool_name,
            username=user.username,
            action="checkin",
            event_time=now,
            job_id=job_id,
            condition=condition_val,
        )
        db.session.add(hist)
        db.session.commit()
        logger.info(f"Tool {tool.tool_id_number} checked in by {user.username}")
        return "success", f"Tool {tool.tool_name} checked in.", extra
    else:
        # Check out
        cal_warning = is_calibration_overdue(tool.tool_calibration_due)
        if cal_warning:
            extra["calibration_warning"] = "This tool is overdue for calibration."
        tool.checked_out_by = user.username
        tool.checkout_time = now
        return_by_dt = None
        if getattr(form, 'return_by', None) and form.return_by.data:
            d = form.return_by.data
            if hasattr(d, 'year'):
                return_by_dt = datetime.combine(d, time(23, 59, 59))
        hist = CheckoutHistory(
            tool_id_number=tool.tool_id_number,
            tool_name=tool.tool_name,
            username=user.username,
            action="checkout",
            event_time=now,
            job_id=job_id,
            condition=condition_val,
            return_by=return_by_dt,
        )
        db.session.add(hist)
        db.session.commit()
        logger.info(f"Tool {tool.tool_id_number} checked out by {user.username}")
        msg = f"Tool {tool.tool_name} checked out."
        if cal_warning:
            msg += " ⚠ Calibration overdue."
        return "success", msg, extra


@bp.route('/checkinout', methods=['GET', 'POST'])
def checkinout():
    form = CheckInOutForm()
    if form.validate_on_submit():
        try:
            status, message, extra = _checkinout_logic(form)
            resp = {"status": status, "message": message}
            if extra:
                resp.update(extra)
            return jsonify(resp)
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("Checkinout database error: %s", e)
            return jsonify(status="error", message="A database error occurred. Please try again."), 500
        except Exception as e:
            db.session.rollback()
            logger.exception("Checkinout error: %s", e)
            return jsonify(status="error", message="An unexpected error occurred. Please try again."), 500
    elif request.method == 'POST':
        logger.debug("Form validation failed: %s", form.errors)
        errs = form.errors
        first = next((v[0] for v in errs.values() if v), "Validation failed")
        return jsonify(status="error", message=first, errors=errs), 400
    return render_template('checkinout.html', form=form, datetime=datetime)


# --- API routes (for future React SPA) ---

@bp.route('/api/health')
def api_health():
    """Health check for API."""
    return jsonify(status="healthy", service="ATEMS", version="1.0.0")


# --- System / Self-Test ---

@bp.route('/api/system/health')
@login_required
def api_system_health():
    """System health with self_test. Cached 60s."""
    from flask import current_app
    from selftest.system import get_system_health
    return jsonify(get_system_health(current_app))


@bp.route('/api/system/run-tests', methods=['POST'])
@login_required
def api_system_run_tests():
    """Run full self-test suite on demand (GUI button)."""
    from selftest.system import run_full_selftest
    return jsonify(run_full_selftest())


@bp.route('/selftest')
@login_required
def selftest_page():
    """Self-Test page: view status, run tests."""
    return render_template('selftest.html')


@bp.route('/logs')
@login_required
def logs_page():
    """Advanced log viewer page."""
    return render_template('logs.html')


@bp.route('/settings')
@login_required
def settings_page():
    """Settings page with categories and presets."""
    return render_template('settings.html')


@bp.route('/reports')
@login_required
def reports_page():
    """Tool reports page: Usage, Calibration, Inventory."""
    return render_template('reports.html')


@bp.route('/import')
@login_required
def import_page():
    """Import tools (and optionally users) from CSV or Excel."""
    return render_template('import.html')


@bp.route('/api/import/preview', methods=['POST'])
@login_required
def api_import_preview():
    """Parse uploaded file and return validated rows + errors (no DB write)."""
    from utils.import_tools import parse_and_validate_tools
    if 'file' not in request.files:
        return jsonify(valid=[], errors=[{"row": 0, "message": "No file uploaded."}]), 200
    f = request.files['file']
    if not f.filename:
        return jsonify(valid=[], errors=[{"row": 0, "message": "No file selected."}]), 200
    try:
        content = f.read()
        valid, errors = parse_and_validate_tools(content, f.filename)
        return jsonify(valid=valid[:100], errors=errors, total_valid=len(valid), total_errors=len(errors))
    except Exception as e:
        return jsonify(valid=[], errors=[{"row": 0, "message": str(e)}]), 200


@bp.route('/api/import/tools', methods=['POST'])
@login_required
def api_import_tools():
    """Import tools from uploaded CSV or Excel. Returns created, updated, errors."""
    from utils.import_tools import parse_and_validate_tools, import_tools_rows
    if 'file' not in request.files:
        return jsonify(created=0, updated=0, errors=[{"row": 0, "message": "No file uploaded."}]), 400
    f = request.files['file']
    if not f.filename:
        return jsonify(created=0, updated=0, errors=[{"row": 0, "message": "No file selected."}]), 400
    try:
        content = f.read()
        valid, parse_errors = parse_and_validate_tools(content, f.filename)
        if parse_errors and not valid:
            return jsonify(created=0, updated=0, errors=parse_errors), 400
        created, updated, import_errors = import_tools_rows(valid)
        all_errors = parse_errors + import_errors
        return jsonify(created=created, updated=updated, errors=all_errors, total=len(valid))
    except Exception as e:
        logger.exception("Import tools failed")
        return jsonify(created=0, updated=0, errors=[{"row": 0, "message": str(e)}]), 400  # noqa: B950


@bp.route('/api/calibration-reminders/status')
@login_required
def api_calibration_reminders_status():
    """Whether email is configured and current counts (overdue, due soon)."""
    from utils.calibration_reminders import (
        is_mail_configured,
        get_reminder_days,
        get_remind_overdue,
        get_due_and_overdue_tools,
    )
    from models.tools import Tools
    tools = Tools.query.filter(
        Tools.tool_calibration_due.isnot(None),
        Tools.tool_calibration_due != "",
        Tools.tool_calibration_due != "N/A",
    ).all()
    overdue, due_soon = get_due_and_overdue_tools(tools)
    return jsonify(
        mail_configured=is_mail_configured(),
        reminder_days=get_reminder_days(),
        remind_overdue=get_remind_overdue(),
        overdue_count=len(overdue),
        due_soon_count=len(due_soon),
        total=len(overdue) + len(due_soon),
    )


@bp.route('/api/calibration-reminders/send', methods=['POST'])
@login_required
def api_calibration_reminders_send():
    """Send calibration reminder email (due/overdue tools). Uses env CALIBRATION_REMIND_* and MAIL_*."""
    from flask import current_app
    from utils.calibration_reminders import send_calibration_reminders
    result = send_calibration_reminders(app=current_app._get_current_object())
    status = 200 if result.get("sent") or result.get("total", 0) == 0 else 400
    return jsonify(result), status


@bp.route('/api/reports/usage')
@login_required
def api_reports_usage():
    """Tool usage report: checkout history with optional date range and limit."""
    from sqlalchemy import and_
    try:
        limit = min(max(1, int(request.args.get('limit', 500))), 2000)
    except (TypeError, ValueError):
        limit = 500
    date_from = request.args.get('date_from')  # YYYY-MM-DD
    date_to = request.args.get('date_to')
    username = request.args.get('username', '').strip()
    tool_id = request.args.get('tool_id', '').strip()
    action = request.args.get('action', '').strip()  # checkout or checkin
    q = CheckoutHistory.query.order_by(CheckoutHistory.event_time.desc())
    if date_from:
        try:
            q = q.filter(CheckoutHistory.event_time >= datetime.strptime(date_from, '%Y-%m-%d'))
        except ValueError:
            pass
    if date_to:
        try:
            end = datetime.strptime(date_to, '%Y-%m-%d')
            from datetime import timedelta
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            q = q.filter(CheckoutHistory.event_time <= end)
        except ValueError:
            pass
    if username:
        q = q.filter(CheckoutHistory.username.ilike(f'%{username}%'))
    if tool_id:
        q = q.filter(CheckoutHistory.tool_id_number.ilike(f'%{tool_id}%'))
    if action:
        q = q.filter(CheckoutHistory.action == action)
    try:
        events = q.limit(limit).all()
        return jsonify(events=[
            {
                'event_time': e.event_time.isoformat() if e.event_time else None,
                'action': e.action,
                'tool_id_number': e.tool_id_number,
                'tool_name': e.tool_name or '',
                'username': e.username,
                'job_id': e.job_id or '',
                'condition': e.condition or '',
                'return_by': e.return_by.isoformat() if getattr(e, 'return_by', None) and e.return_by else None,
            }
            for e in events
        ], count=len(events))
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("api_reports_usage: %s", e)
        return jsonify(error="Database error", events=[], count=0), 500


@bp.route('/api/reports/calibration')
@login_required
def api_reports_calibration():
    """Calibration report: tools due, overdue, by category."""
    from utils.calibration import is_calibration_overdue
    cal_tools = Tools.query.filter(
        Tools.tool_calibration_due != 'N/A',
        Tools.tool_calibration_due.isnot(None),
    ).order_by(Tools.tool_calibration_due).all()
    overdue = []
    due_soon = []
    for t in cal_tools:
        row = {
            'tool_id_number': t.tool_id_number,
            'tool_name': t.tool_name,
            'tool_location': t.tool_location,
            'category': t.category or '',
            'tool_calibration_due': t.tool_calibration_due,
            'tool_status': t.tool_status,
        }
        if is_calibration_overdue(t.tool_calibration_due):
            overdue.append(row)
        else:
            due_soon.append(row)
    return jsonify(overdue=overdue, due_soon=due_soon, overdue_count=len(overdue), due_soon_count=len(due_soon))


@bp.route('/api/reports/overdue-returns')
@login_required
def api_reports_overdue_returns():
    """Overdue returns: tools currently checked out past their return-by date (bulk query)."""
    from datetime import timezone
    from utils.performance import get_overdue_returns_bulk
    _now = datetime.now(timezone.utc).replace(tzinfo=None)
    tools_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).all()
    raw = get_overdue_returns_bulk(tools_out, _now, Tools, CheckoutHistory)
    overdue = [
        {
            "tool_id_number": r["tool_id_number"],
            "tool_name": r["tool_name"],
            "username": r["username"],
            "return_by": r["return_by"].isoformat() if r["return_by"] else None,
        }
        for r in raw
    ]
    return jsonify(overdue=overdue, count=len(overdue))


@bp.route('/api/reports/inventory')
@login_required
def api_reports_inventory():
    """Inventory report: tools by status and category."""
    from sqlalchemy import func
    total = Tools.query.count()
    checked_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).count()
    in_stock = total - checked_out
    by_category_rows = db.session.query(
        Tools.category,
        func.count(Tools.id).label('total'),
    ).filter(Tools.category.isnot(None), Tools.category != '').group_by(Tools.category).order_by(func.count(Tools.id).desc()).all()
    out_by_cat = db.session.query(
        Tools.category,
        func.count(Tools.id).label('out'),
    ).filter(Tools.category.isnot(None), Tools.category != '', Tools.checked_out_by.isnot(None)).group_by(Tools.category).all()
    out_map = {c[0]: c[1] for c in out_by_cat}
    by_category = [{'category': c[0], 'total': c[1], 'checked_out': out_map.get(c[0], 0), 'in_stock': c[1] - out_map.get(c[0], 0)} for c in by_category_rows]
    by_status = db.session.query(Tools.tool_status, func.count(Tools.id)).group_by(Tools.tool_status).all()
    return jsonify(
        total=total,
        in_stock=in_stock,
        checked_out=checked_out,
        by_category=by_category,
        by_status=[{'status': s[0], 'count': s[1]} for s in by_status],
    )


@bp.route('/api/reports/export')
@login_required
def api_reports_export():
    """Export report as CSV, PDF, or Excel (format=csv|pdf|xlsx)."""
    from flask import Response
    import csv
    import io

    report_type = request.args.get('type', 'usage')
    fmt = request.args.get('format', 'csv').lower()
    if fmt not in ('csv', 'pdf', 'xlsx'):
        fmt = 'csv'

    if report_type == 'usage':
        try:
            limit = min(max(1, int(request.args.get('limit', 2000))), 5000)
        except (TypeError, ValueError):
            limit = 2000
        try:
            events = CheckoutHistory.query.order_by(CheckoutHistory.event_time.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("api_reports_export usage: %s", e)
            return jsonify(error="Database error"), 500
        headers = ['Event Time', 'Action', 'Tool ID', 'Tool Name', 'User', 'Job ID', 'Condition', 'Return By']
        rows = [
            [
                e.event_time.strftime('%Y-%m-%d %H:%M') if e.event_time else '',
                e.action,
                e.tool_id_number or '',
                e.tool_name or '',
                e.username or '',
                e.job_id or '',
                e.condition or '',
                e.return_by.strftime('%Y-%m-%d') if getattr(e, 'return_by', None) and e.return_by else '',
            ]
            for e in events
        ]
        try:
            if fmt == 'pdf':
                from utils.report_export import pdf_table
                data = pdf_table(headers, rows, title="ATEMS Tool Usage Report")
                return Response(data, mimetype='application/pdf', headers={'Content-Disposition': 'attachment; filename=atems_usage_report.pdf'})
            if fmt == 'xlsx':
                from utils.report_export import xlsx_table
                data = xlsx_table(headers, rows, sheet_name="Usage")
                return Response(data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=atems_usage_report.xlsx'})
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(headers)
            for r in rows:
                w.writerow(r)
            return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=atems_usage_report.csv'})
        except Exception as ex:
            logger.exception("api_reports_export usage %s: %s", fmt, ex)
            return jsonify(error="Export failed. Please try again."), 500
    elif report_type == 'overdue-returns':
        from datetime import timezone
        from utils.performance import get_overdue_returns_bulk
        _now = datetime.now(timezone.utc).replace(tzinfo=None)
        tools_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).all()
        raw = get_overdue_returns_bulk(tools_out, _now, Tools, CheckoutHistory)
        headers = ['Tool ID', 'Tool Name', 'Checked out by', 'Return by']
        rows = [
            [
                r["tool_id_number"] or '',
                r["tool_name"] or '',
                r["username"] or '',
                r["return_by"].strftime('%Y-%m-%d') if r["return_by"] else '',
            ]
            for r in raw
        ]
        try:
            if fmt == 'pdf':
                from utils.report_export import pdf_table
                data = pdf_table(headers, rows, title="ATEMS Overdue Returns")
                return Response(data, mimetype='application/pdf', headers={'Content-Disposition': 'attachment; filename=atems_overdue_returns.pdf'})
            if fmt == 'xlsx':
                from utils.report_export import xlsx_table
                data = xlsx_table(headers, rows, sheet_name="Overdue Returns")
                return Response(data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=atems_overdue_returns.xlsx'})
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(headers)
            for r in rows:
                w.writerow(r)
            return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=atems_overdue_returns.csv'})
        except Exception as ex:
            logger.exception("api_reports_export overdue-returns %s: %s", fmt, ex)
            return jsonify(error="Export failed. Please try again."), 500
    elif report_type == 'calibration':
        from utils.calibration import is_calibration_overdue
        cal_tools = Tools.query.filter(
            Tools.tool_calibration_due != 'N/A',
            Tools.tool_calibration_due.isnot(None),
        ).order_by(Tools.tool_calibration_due).all()
        headers = ['Tool ID', 'Tool Name', 'Location', 'Category', 'Calibration Due', 'Status', 'Overdue']
        rows = [
            [
                t.tool_id_number,
                t.tool_name or '',
                t.tool_location or '',
                t.category or '',
                t.tool_calibration_due or '',
                t.tool_status or '',
                'Yes' if is_calibration_overdue(t.tool_calibration_due) else 'No',
            ]
            for t in cal_tools
        ]
        try:
            if fmt == 'pdf':
                from utils.report_export import pdf_table
                data = pdf_table(headers, rows, title="ATEMS Calibration Report")
                return Response(data, mimetype='application/pdf', headers={'Content-Disposition': 'attachment; filename=atems_calibration_report.pdf'})
            if fmt == 'xlsx':
                from utils.report_export import xlsx_table
                data = xlsx_table(headers, rows, sheet_name="Calibration")
                return Response(data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=atems_calibration_report.xlsx'})
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(headers)
            for r in rows:
                w.writerow(r)
            return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=atems_calibration_report.csv'})
        except Exception as ex:
            logger.exception("api_reports_export calibration %s: %s", fmt, ex)
            return jsonify(error="Export failed. Please try again."), 500
    elif report_type == 'inventory':
        tools = Tools.query.order_by(Tools.category, Tools.tool_id_number).all()
        headers = ['Tool ID', 'Tool Name', 'Location', 'Category', 'Status', 'Checked Out By', 'Calibration Due']
        rows = [
            [
                t.tool_id_number,
                t.tool_name or '',
                t.tool_location or '',
                t.category or '',
                t.tool_status or '',
                t.checked_out_by or '',
                t.tool_calibration_due or '',
            ]
            for t in tools
        ]
        try:
            if fmt == 'pdf':
                from utils.report_export import pdf_table
                data = pdf_table(headers, rows, title="ATEMS Inventory Report")
                return Response(data, mimetype='application/pdf', headers={'Content-Disposition': 'attachment; filename=atems_inventory_report.pdf'})
            if fmt == 'xlsx':
                from utils.report_export import xlsx_table
                data = xlsx_table(headers, rows, sheet_name="Inventory")
                return Response(data, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=atems_inventory_report.xlsx'})
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(headers)
            for r in rows:
                w.writerow(r)
            return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=atems_inventory_report.csv'})
        except Exception as ex:
            logger.exception("api_reports_export inventory %s: %s", fmt, ex)
            return jsonify(error="Export failed. Please try again."), 500
    return jsonify(error='Invalid report type'), 400


@bp.route('/api/logs')
@login_required
def api_logs():
    """API endpoint for log retrieval with filtering."""
    try:
        import os
        
        # Get parameters (validate to avoid ValueError)
        try:
            limit = min(max(1, int(request.args.get('limit', 250))), 1000)
        except (TypeError, ValueError):
            limit = 250
        level = request.args.get('level', '').upper()
        search = request.args.get('search', '').lower()
        
        # Read atems.log
        log_file = os.path.join(os.path.dirname(__file__), 'atems.log')
        if not os.path.exists(log_file):
            return jsonify({'logs': [], 'count': 0})
        
        # Parse log file
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f.readlines()[-limit*2:]:  # Read more than limit to account for filtering
                line = line.strip()
                if not line:
                    continue
                
                # Parse log format: "timestamp - name - level - message"
                try:
                    parts = line.split(' - ', 3)
                    if len(parts) >= 4:
                        timestamp, name, log_level, message = parts
                        
                        # Apply filters
                        if level and log_level != level:
                            continue
                        if search and search not in message.lower():
                            continue
                        
                        logs.append({
                            'timestamp': timestamp,
                            'name': name,
                            'level': log_level,
                            'message': message
                        })
                except Exception as parse_err:
                    logger.debug("Log line parse failed: %s", parse_err)
                    # If parsing fails, include raw line
                    logs.append({
                        'timestamp': '',
                        'name': '',
                        'level': 'INFO',
                        'message': line
                    })
        
        # Limit results
        logs = logs[-limit:]
        
        return jsonify({
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({'error': str(e), 'logs': [], 'count': 0}), 500


@bp.route('/api/stats')
@login_required
def api_stats():
    """Inventory stats for dashboard (tools out, overdue, calibration due)."""
    from utils.calibration import is_calibration_overdue

    try:
        total = Tools.query.count()
        checked_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).count()
        in_stock = total - checked_out
        cal_tools = Tools.query.filter(
            Tools.tool_calibration_due != "N/A",
            Tools.tool_calibration_due.isnot(None),
        ).all()
        calibration_overdue = sum(1 for t in cal_tools if is_calibration_overdue(t.tool_calibration_due))
        return jsonify(
            total_tools=total,
            checked_out=checked_out,
            in_stock=in_stock,
            calibrated_tools=len(cal_tools),
            calibration_overdue=calibration_overdue,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("api_stats: %s", e)
        return jsonify(error="Database error"), 500


@bp.route('/api/history')
@login_required
def api_history():
    """Recent check-in/check-out events for audit trail."""
    try:
        limit = min(max(1, int(request.args.get("limit", 20))), 100)
    except (TypeError, ValueError):
        limit = 20
    try:
        events = (
            CheckoutHistory.query.order_by(CheckoutHistory.event_time.desc()).limit(limit).all()
        )
        return jsonify(events=[
            {
                "event_time": e.event_time.isoformat() if e.event_time else None,
                "action": e.action,
                "tool_id_number": e.tool_id_number,
                "tool_name": e.tool_name,
                "username": e.username,
                "job_id": e.job_id,
                "condition": e.condition,
            }
            for e in events
        ])
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("api_history: %s", e)
        return jsonify(error="Database error", events=[]), 500


@bp.route('/api/tools')
@login_required
def api_tools():
    """List tools (optional filters: status, checked_out)."""
    try:
        status = request.args.get("status")
        checked_out = request.args.get("checked_out")
        q = Tools.query
        if status:
            q = q.filter(Tools.tool_status == status)
        if checked_out == "true":
            q = q.filter(Tools.checked_out_by.isnot(None))
        elif checked_out == "false":
            q = q.filter(Tools.checked_out_by.is_(None))
        tools = q.order_by(Tools.tool_name).limit(100).all()
        return jsonify(tools=[
            {
                "id": t.id,
                "tool_id_number": t.tool_id_number,
                "tool_name": t.tool_name,
                "tool_location": t.tool_location,
                "tool_status": t.tool_status,
                "checked_out_by": t.checked_out_by,
                "tool_calibration_due": t.tool_calibration_due,
            }
            for t in tools
        ])
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("api_tools: %s", e)
        return jsonify(error="Database error", tools=[]), 500


@bp.route('/api/user-by-badge')
def api_user_by_badge():
    """Look up username by badge_id (for scan flow: fill username when badge is scanned)."""
    badge_id = (request.args.get("badge_id") or "").strip()
    if not badge_id:
        return jsonify(username=None), 200
    user = User.query.filter_by(badge_id=badge_id).first()
    if not user:
        return jsonify(username=None), 200
    return jsonify(username=user.username)


@bp.route('/api/checkinout', methods=['POST'])
def api_checkinout():
    """JSON API for check-in/check-out (scan-gun, mobile)."""
    data = request.get_json() or {}
    username = data.get("username") or request.form.get("username")
    badge_id = data.get("badge_id") or request.form.get("badge_id")
    tool_id_number = data.get("tool_id_number") or request.form.get("tool_id_number")
    job_id = data.get("job_id") or request.form.get("job_id")
    condition = data.get("condition") or request.form.get("condition")
    return_by = data.get("return_by") or request.form.get("return_by")
    form_data = {
        "username": username,
        "badge_id": badge_id,
        "tool_id_number": tool_id_number,
        "job_id": job_id or "",
        "condition": condition or "",
    }
    if return_by:
        form_data["return_by"] = return_by
    form = CheckInOutForm(data=form_data)
    if not form.validate():
        first = next((v[0] for v in form.errors.values() if v), "Validation failed")
        return jsonify(status="error", message=first, errors=form.errors), 400
    try:
        status, message, extra = _checkinout_logic(form)
        resp = {"status": status, "message": message}
        if extra:
            resp.update(extra)
        if status == "success":
            resp["action"] = "checkin" if "checked in" in message.lower() else "checkout"
            return jsonify(resp)
        return jsonify(status=status, message=message), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("api_checkinout database error: %s", e)
        return jsonify(status="error", message="A database error occurred. Please try again."), 500
    except Exception as e:
        db.session.rollback()
        logger.exception("api_checkinout error: %s", e)
        return jsonify(status="error", message="An unexpected error occurred. Please try again."), 500
