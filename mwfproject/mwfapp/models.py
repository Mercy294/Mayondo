from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('SALES_AGENT', 'Sales Agent'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.email}) ({self.phone})  ({self.get_role_display()})"


class Stock(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    quantity = models.IntegerField()
    category = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    cost_price = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=1)
    supplier = models.CharField(max_length=100)
    date_added = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.category})"


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('Mobile Money', 'Mobile Money'),
        ('Cheque', 'Cheque'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    STATUS_CHOICES = [
        ('TOTAL', 'Total'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    # product = models.CharField(max_length=100)
    stock_item = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="sales")
    quantity_sold = models.PositiveIntegerField()
    sale_price = models.DecimalField(max_digits=10, decimal_places=1)
    customer_name = models.CharField(max_length=100)
    transport = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    date = models.DateField(default=date.today)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='Cash', blank=True)
    sales_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def save(self, *args, **kwargs):
        if self.transport == 0:
            self.transport = Decimal(self.sale_price) * Decimal('0.05')
            self.total_price = self.sale_price + self.transport
        super().save(*args, **kwargs)

    @property
    def amount(self):
        return (self.sale_price * self.quantity_sold) + self.transport

    def __str__(self):
        return f"{self.product} sold to {self.customer_name} by {self.sales_agent} on {self.date}"
