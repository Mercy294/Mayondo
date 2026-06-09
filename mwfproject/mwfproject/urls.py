from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from mwfapp import views

urlpatterns = [
    # home & admin
    path("admin/", admin.site.urls),
    path("", views.homePage, name="homePage"),
    path("login/", views.loginPage, name="loginPage"),
    path("register/", views.registerPage, name="registerPage"),
    path("dashboard/", views.dashboardPage, name="dashboardPage"),
    path("recordsales/", views.recordSales, name="recordSales"),
    path("sales/", views.salesPage, name="salesPage"),
    path("viewsales/<str:sale_id>/", views.viewSales, name="viewSales"),
    path("editsales/<str:sale_id>/", views.editSales, name="editSales"),
    path("deletesales/<str:sale_id>/", views.deleteSales, name="deleteSales"),
    path("recordstocks/", views.recordStocks, name="recordStocks"),
    path("stocks/", views.stocksPage, name="stocksPage"),
    path("viewstocks/<str:stock_id>/", views.viewStocks, name="viewStocks"),
    path("editstocks/<str:stock_id>/", views.editStocks, name="editStocks"),
    path("deletestocks/<str:stock_id>/", views.deleteStocks, name="deleteStocks"),
    # path('addusers/', views.addUser, name='addUser'),
    path("users/", views.usersPage, name="usersPage"),
    path("viewuser/<str:user_id>/", views.viewUser, name="viewUser"),
    path("edituser/<str:user_id>/", views.editUser, name="editUser"),
    path("deleteuser/<str:user_id>/", views.deleteUser, name="deleteUser"),
    path("logout/", views.logoutPage, name="logoutPage"),
    path("salesreport", views.sales_report, name="sales_report"),
    path("stocksreport", views.stocks_report, name="stocks_report"),
    path("print_receipt/<int:sale_id>/", views.print_receipt, name="print_receipt"),
]

# Serve static files during production (when DEBUG=False)
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
