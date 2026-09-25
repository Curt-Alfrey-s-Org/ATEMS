#   notify.py


from extensions import admin, SecureBaseView
from flask_admin.base import expose





class NotificationsView(SecureBaseView):
    """View for notifications"""
    @expose('/')
    def index(self):
        return self.render('admin/notify.html')   
    
 
admin.add_view(NotificationsView(name='Notifications', endpoint='notify'))


