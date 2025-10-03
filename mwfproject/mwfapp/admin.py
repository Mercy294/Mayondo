from django.contrib import admin
from .models import Stock, Sale, User  # import your custom user
from django.contrib.auth.admin import UserAdmin

# unregister the user model if already registered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Extend Django’s built-in UserAdmin so your custom fields show up
class CustomUserAdmin(UserAdmin):
    # Fields to display in the list view
    list_display = ("email", "first_name", "last_name", "role", "is_staff", "is_active", "date_joined", "last_login", )
    list_filter = ("role", "is_staff", "is_active")
    # Fields to search
    search_fields = ("email", "role")
    # Fieldsets = how fields are grouped in the edit form
    fieldsets = UserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("role",)}),
    )

# Register your models here.
admin.site.register(Stock)
admin.site.register(Sale)
# Register your custom user
admin.site.register(User, CustomUserAdmin)
