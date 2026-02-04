#   notify.py


from extensions import admin
from flask_admin.base import BaseView, expose





class NotificationsView(BaseView):
    """View for notifications"""
    @expose('/')
    def index(self):
        return self.render('admin/notify.html')   
    
 
admin.add_view(NotificationsView(name='Notifications', endpoint='notify'))


