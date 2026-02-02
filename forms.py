from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateTimeField, SelectField
from wtforms.validators import DataRequired, ValidationError, Optional
from datetime import datetime

# Custom validators
def validate_tool_id(form, field):
    """Tool ID: 1-64 chars, alphanumeric + hyphens (industry format e.g. CONS-HAM-001)."""
    s = (field.data or "").strip()
    if not s or len(s) > 64:
        raise ValidationError('Tool ID must be 1-64 characters.')
    if not all(c.isalnum() or c == '-' for c in s):
        raise ValidationError('Tool ID may only contain letters, numbers, and hyphens.')

def validate_badge_id(form, field):
    if not field.data.isalnum():  # Example: Badge ID must be alphanumeric
        raise ValidationError('Badge ID must be alphanumeric.')

class CheckInForm(FlaskForm):
    tool_id_number = StringField('Tool ID', validators=[DataRequired(), validate_tool_id])
    checkin_time = DateTimeField('Check In Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(CheckInForm, self).__init__(*args, **kwargs)
        self.checkin_time.data = datetime.now()

CONDITION_CHOICES = [("", "— Select (optional) —"), ("Good", "Good"), ("Fair", "Fair"), ("Damaged", "Damaged")]


class CheckInOutForm(FlaskForm):
    """Combined form for check-in/check-out (badge + tool scan)."""
    username = StringField('Username', validators=[DataRequired()])
    badge_id = StringField('Badge ID', validators=[DataRequired(), validate_badge_id])
    tool_id_number = StringField('Tool ID', validators=[DataRequired(), validate_tool_id])
    job_id = StringField('Job/Project ID', validators=[Optional()])
    condition = SelectField('Condition', choices=CONDITION_CHOICES, validators=[Optional()])
    submit = SubmitField('Submit')

class CheckOutForm(FlaskForm):
    username_or_badge_id = StringField('Username or Badge ID', validators=[DataRequired(), validate_badge_id])
    tool_id_number = StringField('Tool ID', validators=[DataRequired(), validate_tool_id])
    checkout_time = DateTimeField('Check Out Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(CheckOutForm, self).__init__(*args, **kwargs)
        self.checkout_time.data = datetime.now()
