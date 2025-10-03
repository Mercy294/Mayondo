# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Stock, Sale, User

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']
    username = forms.CharField(error_messages={"required": "Please Enter the username"})
    email = forms.EmailField(error_messages={"required": "Please Enter the email"})
    password1 = forms.CharField(error_messages={"required": "Please Enter the password"})
    password2 = forms.CharField(error_messages={"required": "Please Enter the same password"})

class UserAuthenticationForm():
    error_messages = {
        "invalid_login": "Please check your credentials and try again"
    }
    username = forms.CharField(error_messages={"required": "Please Enter the username"})
    password = forms.CharField(
        error_messages={"required": "Please Enter a valid password"}
    )

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            "name",
            "type",
            "quantity",
            "color",
            "cost_price",
            "selling_price",
            "supplier",
            "date",
            "category",
        ]

class SaleForm(forms.ModelForm):
    class Meta:
        models = Sale
        fields = [
            "product", 
            "quantity_sold", 
            "sale_price", 
            "customer_name", 
            "transport", 
            "total_price", 
            "date", 
            "payment_method", 
            "sales_agent", 
            "status",
        ]
