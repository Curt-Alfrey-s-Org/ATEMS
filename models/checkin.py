#   checkin.py


from extensions import admin
from flask_admin.base import BaseView, expose



class CheckinView(BaseView):
    """View for checkin"""
    @expose('/')
    def index(self):
        return self.render('checkin.html')
    
   


admin.add_view(CheckinView(name='Check In Tools', endpoint='checkin'))
