# checkout_history.py - Audit trail for check-in/check-out events

from extensions import admin, db
from flask_admin.contrib.sqla import ModelView
from datetime import datetime


class CheckoutHistory(db.Model):
    """Log of every check-in and check-out event."""
    __tablename__ = "checkout_history"

    id = db.Column(db.Integer, primary_key=True)
    tool_id_number = db.Column(db.String(64), nullable=False, index=True)
    tool_name = db.Column(db.String(64), nullable=True)
    username = db.Column(db.String(128), nullable=False, index=True)
    action = db.Column(db.String(16), nullable=False)  # 'checkout' or 'checkin'
    event_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    job_id = db.Column(db.String(64), nullable=True)
    condition = db.Column(db.String(32), nullable=True)  # Good, Fair, Damaged at check-in/out

    def __repr__(self):
        return f"<CheckoutHistory {self.action} {self.tool_id_number} by {self.username} at {self.event_time}>"


class CheckoutHistoryView(ModelView):
    column_list = ("event_time", "action", "tool_id_number", "tool_name", "username", "job_id", "condition")
    column_sortable_list = ("event_time", "action", "tool_id_number", "username", "job_id")
    column_default_sort = ("event_time", True)
    column_filters = ("action", "username", "tool_id_number", "condition")
    column_searchable_list = ("tool_id_number", "tool_name", "username", "job_id")
    
    def is_accessible(self):
        """Only admins can access Flask-Admin panel."""
        from flask_login import current_user
        return current_user.is_authenticated and current_user.is_admin()
    
    def inaccessible_callback(self, name, **kwargs):
        """Redirect if not accessible."""
        from flask import redirect, url_for, flash
        from flask_login import current_user
        if current_user.is_authenticated:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('main.login'))


admin.add_view(CheckoutHistoryView(CheckoutHistory, db.session, name="Checkout History"))
