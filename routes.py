from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from forms import CheckInOutForm
from models import User, Tools, CheckoutHistory
from extensions import db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from utils.calibration import is_calibration_overdue
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


@bp.app_context_processor
def inject_datetime():
    return {'datetime': datetime}


@bp.route('/')
def index():
    """Landing page - show splash screen if not logged in, else dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('splash.html')


@bp.route('/splash')
def splash():
    """Professional splash screen for demo site."""
    return render_template('splash.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with stat cards, category breakdown, usage trend, and recent activity."""
    from utils.calibration import is_calibration_overdue
    from sqlalchemy import func
    from datetime import timedelta, timezone

    _now = datetime.now(timezone.utc).replace(tzinfo=None)
    total = Tools.query.count()
    checked_out = Tools.query.filter(Tools.checked_out_by.isnot(None)).count()
    in_stock = total - checked_out
    cal_tools = Tools.query.filter(
        Tools.tool_calibration_due != "N/A",
        Tools.tool_calibration_due.isnot(None),
    ).all()
    calibration_overdue = sum(1 for t in cal_tools if is_calibration_overdue(t.tool_calibration_due))
    recent = CheckoutHistory.query.order_by(CheckoutHistory.event_time.desc()).limit(10).all()

    # Category breakdown (tools per category)
    category_breakdown = db.session.query(
        Tools.category, func.count(Tools.id).label('count')
    ).filter(Tools.category.isnot(None), Tools.category != '').group_by(Tools.category).order_by(func.count(Tools.id).desc()).all()
    category_breakdown = [{'name': c[0], 'count': c[1]} for c in category_breakdown]

    # Usage trend: checkouts per day for last 7 days
    seven_days_ago = _now - timedelta(days=7)
    usage_rows = db.session.query(
        func.date(CheckoutHistory.event_time).label('day'),
        func.count(CheckoutHistory.id).label('count')
    ).filter(
        CheckoutHistory.event_time >= seven_days_ago,
        CheckoutHistory.action == 'checkout'
    ).group_by(func.date(CheckoutHistory.event_time)).order_by('day').all()
    usage_trend = [{'day': str(r[0]), 'count': r[1]} for r in usage_rows]

    # Calibration summary: overdue, due in 30/60/90 days (string compare YYYY-MM-DD)
    today = _now
    d30 = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    d60 = (today + timedelta(days=60)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')
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

    # Categories list for filter
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
    )


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next') or url_for('main.dashboard')
            return redirect(next_page)
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


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
        hist = CheckoutHistory(
            tool_id_number=tool.tool_id_number,
            tool_name=tool.tool_name,
            username=user.username,
            action="checkout",
            event_time=now,
            job_id=job_id,
            condition=condition_val,
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
            logger.error(f"Database error: {str(e)}")
            return jsonify(status="error", message="A database error occurred. Please try again.")
    elif request.method == 'POST':
        logger.warning(f"Form validation failed: {form.errors}")
        errs = form.errors
        first = next((v[0] for v in errs.values() if v), "Validation failed")
        return jsonify(status="error", message=first, errors=errs), 400
    return render_template('checkinout.html', form=form, datetime=datetime)


# --- API routes (for future React SPA) ---

@bp.route('/api/health')
def api_health():
    """Health check for API."""
    return jsonify(status="healthy", service="ATEMS", version="1.0.0")


# --- System / Self-Test (integrated like Rankings-Bot) ---

@bp.route('/api/system/health')
@login_required
def api_system_health():
    """System health with self_test. Cached 60s. Matches Rankings-Bot /api/system/health shape."""
    from flask import current_app
    from selftest.system import get_system_health
    return jsonify(get_system_health(current_app))


@bp.route('/api/system/run-tests', methods=['POST'])
@login_required
def api_system_run_tests():
    """Run full self-test suite on demand (GUI button). Matches Rankings-Bot POST /api/system/run-tests."""
    from selftest.system import run_full_selftest
    return jsonify(run_full_selftest())


@bp.route('/selftest')
@login_required
def selftest_page():
    """Self-Test page: view status, run tests (like Rankings-Bot SelfTestPanel)."""
    return render_template('selftest.html')


@bp.route('/logs')
@login_required
def logs_page():
    """Advanced log viewer page (adapted from Rankings-Bot)."""
    return render_template('logs.html')


@bp.route('/settings')
@login_required
def settings_page():
    """Settings page with categories and presets (adapted from Rankings-Bot)."""
    return render_template('settings.html')


@bp.route('/reports')
@login_required
def reports_page():
    """Tool reports page: Usage, Calibration, Inventory."""
    return render_template('reports.html')


@bp.route('/api/reports/usage')
@login_required
def api_reports_usage():
    """Tool usage report: checkout history with optional date range and limit."""
    from sqlalchemy import and_
    limit = min(int(request.args.get('limit', 500)), 2000)
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
        }
        for e in events
    ], count=len(events))


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
    """Export report as CSV."""
    report_type = request.args.get('type', 'usage')
    if report_type == 'usage':
        limit = min(int(request.args.get('limit', 2000)), 5000)
        events = CheckoutHistory.query.order_by(CheckoutHistory.event_time.desc()).limit(limit).all()
        from flask import Response
        import csv
        import io
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Event Time', 'Action', 'Tool ID', 'Tool Name', 'User', 'Job ID', 'Condition'])
        for e in events:
            w.writerow([
                e.event_time.strftime('%Y-%m-%d %H:%M') if e.event_time else '',
                e.action,
                e.tool_id_number or '',
                e.tool_name or '',
                e.username or '',
                e.job_id or '',
                e.condition or '',
            ])
        return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=atems_usage_report.csv'})
    elif report_type == 'calibration':
        from utils.calibration import is_calibration_overdue
        from flask import Response
        import csv
        import io
        cal_tools = Tools.query.filter(
            Tools.tool_calibration_due != 'N/A',
            Tools.tool_calibration_due.isnot(None),
        ).order_by(Tools.tool_calibration_due).all()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Tool ID', 'Tool Name', 'Location', 'Category', 'Calibration Due', 'Status', 'Overdue'])
        for t in cal_tools:
            w.writerow([
                t.tool_id_number,
                t.tool_name or '',
                t.tool_location or '',
                t.category or '',
                t.tool_calibration_due or '',
                t.tool_status or '',
                'Yes' if is_calibration_overdue(t.tool_calibration_due) else 'No',
            ])
        return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=atems_calibration_report.csv'})
    elif report_type == 'inventory':
        from flask import Response
        import csv
        import io
        tools = Tools.query.order_by(Tools.category, Tools.tool_id_number).all()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['Tool ID', 'Tool Name', 'Location', 'Category', 'Status', 'Checked Out By', 'Calibration Due'])
        for t in tools:
            w.writerow([
                t.tool_id_number,
                t.tool_name or '',
                t.tool_location or '',
                t.category or '',
                t.tool_status or '',
                t.checked_out_by or '',
                t.tool_calibration_due or '',
            ])
        return Response(buf.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=atems_inventory_report.csv'})
    return jsonify(error='Invalid report type'), 400


@bp.route('/api/logs')
@login_required
def api_logs():
    """API endpoint for log retrieval with filtering."""
    try:
        import os
        
        # Get parameters
        limit = int(request.args.get('limit', 250))
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
                except:
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


@bp.route('/api/history')
@login_required
def api_history():
    """Recent check-in/check-out events for audit trail."""
    limit = min(int(request.args.get("limit", 20)), 100)
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


@bp.route('/api/tools')
@login_required
def api_tools():
    """List tools (optional filters: status, checked_out)."""
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


@bp.route('/api/checkinout', methods=['POST'])
def api_checkinout():
    """JSON API for check-in/check-out (scan-gun, mobile)."""
    data = request.get_json() or {}
    username = data.get("username") or request.form.get("username")
    badge_id = data.get("badge_id") or request.form.get("badge_id")
    tool_id_number = data.get("tool_id_number") or request.form.get("tool_id_number")
    job_id = data.get("job_id") or request.form.get("job_id")
    condition = data.get("condition") or request.form.get("condition")
    form = CheckInOutForm(
        data={
            "username": username,
            "badge_id": badge_id,
            "tool_id_number": tool_id_number,
            "job_id": job_id or "",
            "condition": condition or "",
        }
    )
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
        logger.error(f"Database error: {str(e)}")
        return jsonify(status="error", message="A database error occurred. Please try again."), 500
