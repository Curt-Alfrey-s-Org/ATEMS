#   checkout.py


from extensions import admin
from flask_admin.base import BaseView, expose



class CheckoutView(BaseView):
    """View for checkout"""
    @expose('/')
    def index(self):
        return self.render('checkout.html')
    
   


admin.add_view(CheckoutView(name='Check Out Tools', endpoint='checkout'))
