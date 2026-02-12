#   tools.py

from extensions import admin, db
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.ajax import AjaxModelLoader
from datetime import datetime






class Tools(db.Model):
    """Model for tools. Supports AFI 21-101 / CTK: positive control, calibration, Master Inventory List (MIL)."""
    id = db.Column(db.Integer, primary_key=True)
    tool_id_number = db.Column(db.String(64), nullable=False)
    tool_name = db.Column(db.String(64), nullable=False)
    tool_location = db.Column(db.String(64), nullable=False)
    tool_status = db.Column(db.String(64), nullable=False)
    tool_calibration_due = db.Column(db.String(64), nullable=False)
    tool_calibration_date = db.Column(db.String(64), nullable=False)
    tool_calibration_cert = db.Column(db.String(64), nullable=False)
    tool_calibration_schedule = db.Column(db.String(64), nullable=False)
    checked_out_by = db.Column(db.String(128), nullable=True)  # username when checked out
    category = db.Column(db.String(64), nullable=True)  # industry/category: Construction, Manufacturing, etc.
    checkout_time = db.Column(db.DateTime, default=datetime.now)
    checkin_time = db.Column(db.DateTime, default=datetime.now)
    
    
    def __repr__(self):
        return '<Tool {}, ID: {}, Location: {}, Status: {}, Calibration Due: {}, Calibration Date: {}, Calibration Cert: {}, Calibration Schedule: {}>'.format(self.tool_name, self.tool_id_number, self.tool_location, self.tool_status, self.tool_calibration_due, self.tool_calibration_date, self.tool_calibration_cert, self.tool_calibration_schedule, self.checkout_time, self.checkin_time)
    
class ToolsView(ModelView):
    """View for tools"""
    column_searchable_list = ['tool_name', 'tool_id_number', 'tool_location', 'category', 'tool_status', 'tool_calibration_due', 'tool_calibration_date', 'tool_calibration_cert', 'tool_calibration_schedule', 'checkout_time', 'checkin_time']
    column_filters = ['tool_name', 'tool_id_number', 'tool_location', 'category', 'tool_status', 'tool_calibration_due', 'tool_calibration_date', 'tool_calibration_cert', 'tool_calibration_schedule', 'checkout_time', 'checkin_time']
    column_editable_list = ['tool_name', 'tool_id_number', 'tool_location', 'category', 'tool_status', 'tool_calibration_due', 'tool_calibration_date', 'tool_calibration_cert', 'tool_calibration_schedule', 'checkout_time', 'checkin_time']
    column_default_sort = ('tool_name', 'tool_id_number', 'tool_location', 'tool_status', True)
    column_sortable_list = ['tool_name', 'tool_id_number', 'tool_location','tool_status', 'tool_calibration_due', 'tool_calibration_date', 'tool_calibration_cert', 'tool_calibration_schedule', 'checkout_time', 'checkin_time']
    column_labels = dict(tool_name='Tool Name', tool_id_number='tool_id_number', tool_location='Tool Location', tool_status='Tool Status', tool_calibration_due='Calibration Due', tool_calibration_date='Calibration Date', tool_calibration_cert='Calibration Cert', tool_calibration_schedule='Calibration Schedule', checkout_time='Checkout Time', checkin_time='Checkin Time')
    column_descriptions = dict(tool_name='Tool Name', tool_id_number='tool_id_number', tool_location='Tool Location', tool_status='Tool Status', tool_calibration_due='Calibration Due', tool_calibration_date='Calibration Date', tool_calibration_cert='Calibration Cert', tool_calibration_schedule='Calibration Schedule', checkout_time='Checkout Time', checkin_time='Checkin Time')
    column_details_list = ['tool_name', 'tool_id_number', 'tool_location','tool_status', 'tool_calibration_due', 'tool_calibration_date', 'tool_calibration_cert', 'tool_calibration_schedule', 'checkout_time', 'checkin_time']
    column_export_list = ['tool_name', 'tool_id_number', 'tool_location','tool_status', 'tool_calibration_due', 'tool_calibration_date', 'tool_calibration_cert', 'tool_calibration_schedule', 'checkout_time', 'checkin_time']
    column_choices = dict(tool_status=[('Calibrated', 'Calibrated'), ('Out of Calibration', 'Out of Calibration'), ('In Repair', 'In Repair'), ('Broken', 'Broken'), ('Serviceable', 'Serviceable'), ('In Use', 'In Use'), ('In Stock', 'In Stock'), ('In Transit', 'In Transit'), ('In Inspection', 'In Inspection'), ('In Test', 'In Test'), ('In Maintenance', 'In Maintenance'), ('In Storage', 'In Storage'), ('In Quarantine', 'In Quarantine'), ('In Repair', 'In Repair'), ('Rejected', 'Rejected')])


    

class ToolNameLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_name.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_name}

class ToolIdNumberLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_id_number.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_id_number}

class ToolLocationLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_location.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_location}
    
class ToolStatusLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_status.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_status}
    
class ToolCalibrationDueLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_calibration_due.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_calibration_due}
    
class ToolCalibrationDateLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_calibration_date.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_calibration_date}
    
class ToolCalibrationCertLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_calibration_cert.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_calibration_cert}


class ToolCalibrationScheduleLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.tool_calibration_schedule.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.tool_calibration_schedule}


class Checkin_timeLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.checkin_time.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.checkin_time}
    
class Checkout_timeLoader(AjaxModelLoader):
    def get_one(self, id):
        return db.session.query(Tools).get(id)

    def get_list(self, term, offset=0, limit=10):
        return db.session.query(Tools).filter(Tools.checkout_time.like('%' + term + '%')).all()

    def format(self, model):
        return {"id": model.id, "text": model.checkout_time}
    
            
    
form_ajax_refs = {
    'tool_name': ToolNameLoader('tool_name', db.session),
    'tool_id_number': ToolIdNumberLoader('tool_id_number', db.session),
    'tool_location': ToolLocationLoader('tool_location', db.session),
    'tool_status': ToolStatusLoader('tool_status', db.session),
    'tool_calibration_due': ToolCalibrationDueLoader('tool_calibration_due', db.session),
    'tool_calibration_date': ToolCalibrationDateLoader('tool_calibration_date', db.session),
    'tool_calibration_cert': ToolCalibrationCertLoader('tool_calibration_cert', db.session),
    'tool_calibration_schedule': ToolCalibrationScheduleLoader('tool_calibration_schedule', db.session),
    'checkin_time': Checkin_timeLoader('checkin_time', db.session),
    'checkout_time': Checkout_timeLoader('checkout_time', db.session),
}

admin.add_view(ModelView(Tools, db.session, name='Add Tools'))
