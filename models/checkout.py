#   checkout.py


from extensions import admin, SecureBaseView
from flask_admin.base import expose



class CheckoutView(SecureBaseView):
    """View for checkout"""
    @expose('/')
    def index(self):
        return self.render('checkout.html')
    
   


admin.add_view(CheckoutView(name='Check Out Tools', endpoint='checkout'))
