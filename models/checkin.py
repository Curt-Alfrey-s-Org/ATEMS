#   checkin.py


from extensions import admin, SecureBaseView
from flask_admin.base import expose



class CheckinView(SecureBaseView):
    """View for checkin"""
    @expose('/')
    def index(self):
        return self.render('checkin.html')
    
   


admin.add_view(CheckinView(name='Check In Tools', endpoint='checkin'))
