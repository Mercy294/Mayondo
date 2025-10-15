# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Stock, Sale, User
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now

today = now().date()
yesterday = today - timedelta(days=1)
class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password1', 'password2', 'role']
    first_name = forms.CharField(error_messages={"required": "Please enter the username"})
    last_name = forms.CharField(
        error_messages={"required": "Please enter the username"}
    )
    email = forms.EmailField(error_messages={"required": "Please enter the email"})
    phone = forms.CharField(error_messages={"required": "Please enter the phone number"})
    password1 = forms.CharField(error_messages={"required": "Please enter the password"})
    password2 = forms.CharField(error_messages={"required": "Please enter the same password"})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # auto-fill username
        user.username = (
            f"{self.cleaned_data['first_name']}{self.cleaned_data['last_name']}".lower()
        )
        if commit:
            user.save()
        return user


class UserAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Please check your credentials and try again"
    }
    username = forms.CharField(error_messages={"required": "Please enter the a valid username"})
    password = forms.CharField(
        error_messages={"required": "Please enter a valid password"}
    )

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = '__all__'
        widgets = {
            "date_added": forms.DateInput(
                attrs={
                    "type": "date",
                    "min": yesterday.isoformat(),
                    "max": today.isoformat(),
                }
            )
        }

    def clean_cost_price(self):
        cost_price = self.cleaned_data.get('cost_price')
        if cost_price is not None and cost_price < 0:
            raise forms.ValidationError("Cost price cannot be negative")
        return cost_price

    def clean_selling_price(self):
        selling_price = self.cleaned_data.get('selling_price')
        if selling_price is not None and selling_price < 0:
            raise forms.ValidationError("Selling price cannot be negative")
        return selling_price

    def clean_date_added(self):
        date = self.cleaned_data.get("date_added")
        if date not in [yesterday, today]:
            raise forms.ValidationError("Stock date must be today or yesterday.")
        return date

    # def clean_date_added(self):
    #     date = self.cleaned_data.get("date_added")
    #     today = timezone.now().date()
    #     yesterday = today - timedelta(days=1)
    #     if date not in [yesterday, today]:
    #         raise forms.ValidationError("Stock date must be today or yesterday.")
    #     return date


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = "__all__"
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "min": yesterday.isoformat(),
                    "max": today.isoformat(),
                }
            )
        }
    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date not in [yesterday, today]:
            raise forms.ValidationError("Date must be today or yesterday.")
        return date
    # def clean_date(self):
    #     date = self.cleaned_data["date"]
    #     today = timezone.now().date()
    #     yesterday = today - timedelta(days=1)
    #     if date not in [yesterday, today]:
    #         raise forms.ValidationError("Date must be today or yesterday.")
    #     return date
