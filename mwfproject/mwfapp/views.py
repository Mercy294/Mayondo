from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.utils.dateparse import parse_date
from .models import User, Stock, Sale
from decimal import Decimal
from django.utils.timezone import now
from datetime import date
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

User = get_user_model()


def homePage(request):
    return render(request, "homepage.html")


def loginPage(request):
    if request.method == "POST":
        username_or_email = request.POST.get("identifier")
        password = request.POST.get("password")

        # Try to authenticate by username
        user = authenticate(request, username=username_or_email, password=password)

        # If failed, try email
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(
                    request, username=user_obj.username, password=password
                )
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)  # log the user in
            return redirect("dashboardPage")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("loginPage")

    return render(request, "login.html")


def registerPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("role")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "register.html", {"error": "Passwords do not match"})

        # check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(
                request, "register.html", {"error": "Username already exists"}
            )
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render(request, "register.html", {"error": "Email already exists"})
        if User.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already exists")
            return render(
                request, "register.html", {"error": "Phone number already exists"}
            )

        # Create the user
        user = User.objects.create_user(
            username=username, password=password, email=email, phone=phone, role=role
        )
        user.save()
        return redirect("dashboardPage")

    return render(request, "register.html")


@login_required(login_url="loginPage")
def dashboardPage(request):
    user = request.user
    # Calculate dashboard values
    total_sales = daily_sales = monthly_sales = total_stock = 0
    latest_sales = Sale.objects.order_by("-date")[:10]

    if user.role in ["ADMIN", "MANAGER", "SALES_AGENT"]:
        total_sales = Sale.objects.count()
        # daily_sales = (
        #     Sale.objects.filter(date=date.today()).aggregate(total=Sum("total_price"))[
        #         "total"
        #     ]
        #     or 0
        # )
        today = date.today()
        today_sales = Sale.objects.filter(date=date.today())
        daily_sales = today_sales.aggregate(total=Sum("total_price"))[
            "total"
        ] or Decimal("0")
        # Monthly sales (including transport)
        monthly_sales = Sale.objects.filter(
            date__year=today.year, date__month=today.month
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0")
        total_stock = Stock.objects.count()  # fetch total items in stock
        latest_sales = Sale.objects.order_by("-date")[:10]  # last 10 sales

    context = {
        "user": user,
        "total_sales": total_sales,
        "daily_total": daily_sales,
        "monthly_sales": monthly_sales,
        "total_stock": total_stock,
        "latest_sales": latest_sales,
    }
    if user.role == "ADMIN":
        return render(request, "dashboard.html", context)

    elif user.role == "MANAGER":
        # Redirect to a manager-specific page
        return render(request, "dashboard.html", context)

    elif user.role == "SALES_AGENT":
        return render(request, "dashboard.html", context)

    else:
        return redirect("loginPage")


def salesPage(request):
    all_sales = Sale.objects.all()
    return render(request, "sales.html", {"all_sales": all_sales})


def stocksPage(request):
    all_stocks = Stock.objects.all()
    return render(request, "stocks.html", {"all_stocks": all_stocks})


def recordSales(request):
    if request.method == "POST":
        stock_id = request.POST.get("stock_item")  # expects stock id from form
        stock_item = get_object_or_404(Stock, id=stock_id)

        quantity_sold = int(request.POST.get("quantity_sold", 0))
        sale_price = Decimal(request.POST.get("sale_price", "0"))
        customer_name = request.POST.get("customer_name")
        payment_method = request.POST.get("payment_method")
        

        try:
            sale = Sale(
                stock_item=stock_item,
                quantity_sold=quantity_sold,
                sale_price=sale_price,
                customer_name=customer_name,
                payment_method=payment_method,
                sales_agent=request.user,
            )
            sale.save()  # model will check stock here
            messages.success(request, "Sale recorded successfully!")
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("recordSales")

        return redirect("salesPage")

    all_stocks = Stock.objects.all()
    return render(request, "record_sales.html", {"all_stocks": all_stocks})


def sales_report(request):
    today = now().date()
    sales_today = Sale.objects.filter(date=today)
    monthly_sales = Sale.objects.filter(date__month=today.month, date__year=today.year)
    all_sales = Sale.objects.all().order_by("-date")

    context = {
        "daily_total": sum(s.amount for s in sales_today),
        "monthly_total": sum(s.amount for s in monthly_sales),
        "all_sales": all_sales,
    }
    return render(request, "salesreport.html", context)
    # if request.method == "POST":
    #     product = request.POST.get("product")
    #     quantity_sold = int(request.POST.get("quantity_sold", 0))
    #     sale_price = Decimal(request.POST.get("sale_price", "0"))
    #     customer_name = request.POST.get("customer_name")
    #     payment_method = request.POST.get("payment_method")
    #     transport = request.POST.get("transport", "no")
    #     total_price = request.POST.get("total_price")
    #     sales_agent = request.user

    #     # calculate transport and total_price
    #     if transport.lower() == "yes":
    #         transport = sale_price * Decimal(0.05)
    #     else:
    #         transport = Decimal("0")

    #     total_price = sale_price + transport

    #     # save the sale
    #     sale = Sale(
    #         product=product,
    #         quantity_sold=quantity_sold,
    #         sale_price=sale_price,
    #         customer_name=customer_name,
    #         payment_method=payment_method,
    #         transport=transport,
    #         total_price=total_price,
    #         sales_agent=request.user,
    #     )
    #     sale.save()
    #     return redirect("salesPage")
    # return render(request, "record_sales.html")


def recordStocks(request):
    if request.method == "POST":
        name = request.POST.get("name")
        type = request.POST.get("type")
        quantity = request.POST.get("quantity")
        category = request.POST.get("category")
        color = request.POST.get("color")
        cost_price = request.POST.get("cost_price")
        selling_price = request.POST.get("selling_price")
        supplier = request.POST.get("supplier")
        date_added = parse_date(request.POST.get("date"))

        if not category:
            messages.error(request, "Category is required.")
            return redirect("recordStocks")
        stock = Stock(
            name=name,
            type=type,
            quantity=quantity,
            category=category,
            color=color,
            cost_price=cost_price,
            selling_price=selling_price,
            supplier=supplier,
            date_added=date_added,
        )
        stock.save()
        return redirect("stocksPage")
    return render(request, "record_stocks.html")


@login_required(login_url="loginPage")
def stocks_report(request):
    all_stocks = Stock.objects.all().order_by("name")

    # Calculate total stock value
    total_value = sum(stock.selling_price * stock.quantity for stock in all_stocks)

    context = {"all_stocks": all_stocks, "total_value": total_value}
    return render(request, "stocksreport.html", context)


def viewSales(request, sale_id):
    sale = Sale.objects.get(id=sale_id)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "view_sales_modal.html", {"sale": sale})
    return render(request, "viewsales.html", {"sale": sale})


def viewStocks(request, stock_id):
    stock = Stock.objects.get(id=stock_id)
    return render(request, "viewstocks.html", {"stock": stock})


def editSales(request, sale_id):
    sale = Sale.objects.get(id=sale_id)
    all_stocks = Stock.objects.all()
    if request.method == "POST":
        stock_id = request.POST.get("stock_item")
        sale.stock_item = get_object_or_404(Stock, id=stock_id)
        #sale.product = request.POST.get("product")
        sale.quantity_sold = int(request.POST.get("quantity_sold", 0))
        sale.sale_price = Decimal(request.POST.get("sale_price", "0"))
        sale.customer_name = request.POST.get("customer_name")
        sale.payment_method = request.POST.get("payment_method")
        sale.transport = request.POST.get("transport", "no")
        sale.sales_agent = request.user

        # Recalculate transport and total_price
        if sale.transport.lower() == "yes":
            sale.transport = sale.sale_price * Decimal("0.05")
        else:
            sale.transport = Decimal("0")

        sale.sales_agent = request.user
        sale.save()
        return redirect("salesPage")
    return render(request, "editsales.html", {"sale": sale, "all_stocks": all_stocks})


def editStocks(request, stock_id):
    stock = Stock.objects.get(id=stock_id)
    if request.method == "POST":
        stock.name = request.POST.get("name")
        stock.type = request.POST.get("type")
        stock.quantity = request.POST.get("quantity")
        stock.category = request.POST.get("category")
        stock.color = request.POST.get("color")
        stock.cost_price = request.POST.get("cost_price")
        stock.selling_price = request.POST.get("selling_price")
        stock.supplier = request.POST.get("supplier")
        stock.save()
        return redirect("stocksPage")
    return render(request, "editstocks.html", {"stock": stock})


def deleteSales(request, sale_id):
    sale = Sale.objects.get(id=sale_id)
    if request.method == 'POST':
        sale.delete()
        return redirect("salesPage")
    context = {
        "sale": sale
    }
    return render(request, 'deletesale.html', context)

def deleteStocks(request, stock_id):
    stock = Stock.objects.get(id=stock_id)
    if request.method == 'POST':
        stock.delete()
        return redirect("stocksPage")
    context = {
        'stock': stock
        }
    return render(request, 'deletestock.html', context)

def addUser(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # Create user
        if User.objects.filter(username=name).exists():
            messages.error(request, "Username already exists.")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")

            user = User.objects.create_user(
                username=name, email=email, password=password, role=role
            )
            user.first_name = name
            user.role = role
            user.save()
            messages.success(request, f"User {name} added successfully!")
            return redirect("addPage")  # or redirect to a users list page

    return render(request, "adduser.html")


def usersPage(request):
    users = User.objects.all()
    return render(request, "users.html", {"users": users})


def editUser(request, user_id):
    user = User.objects.get(id=user_id)
    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.role = request.POST.get("role")
        password = request.POST.get("password")
        if password:
            user.set_password(password)  # Update password only if provided
        user.save()
        return redirect("usersPage")
    return render(request, "edit_user.html", {"user": user})


def viewUser(request, user_id):
    user = User.objects.get(id=user_id)
    return render(request, "view_user.html", {"user": user})


def deleteUser(request, user_id):
    user = User.objects.get(id=user_id)
    user.delete()
    return redirect("usersPage")


def logoutPage(request):
    logout(request)
    return redirect("loginPage")
