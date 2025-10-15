# Import necessary Django and Python modules
from django.shortcuts import render, redirect, get_object_or_404  # Rendering templates, redirects, and fetching objects
from django.contrib.auth import authenticate, login, logout, get_user_model  # Authentication functions
from django.contrib import messages  # Display messages to users
from django.utils.dateparse import parse_date  # Convert string dates to date objects
from .models import User, Stock, Sale  # Import custom models
from decimal import Decimal  # Handle decimal numbers precisely (prices, totals)
from django.utils.timezone import now  # Get current date/time in timezone-aware manner
from datetime import date, timedelta  # Standard date/time manipulations
from django.db.models import Sum  # Aggregate sums from querysets
from django.contrib.auth.decorators import login_required # Protect views requiring login
from .forms import UserForm, UserAuthenticationForm  # Import forms for users
from django.core.paginator import Paginator  # Paginate querysets
import json  # Handle JSON data
from django.db.models.functions import TruncMonth  # For grouping by month in queries
from django.views.decorators.cache import never_cache

# Get the custom User model for authentication
User = get_user_model()

# Home page view
def homePage(request):
    """Render the homepage template."""
    return render(request, "homepage.html")


# Login page view
def loginPage(request):
    """
    Handle user login.
    - Authenticate by username or email.
    - Display error if credentials are invalid.
    """
    if request.method == "POST":
        # Get form inputs
        username_or_email = request.POST.get("identifier")
        password = request.POST.get("password")

        # First, try authentication using username
        user = authenticate(request, username=username_or_email, password=password)

        # If username login fails, try using email
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(
                    request, username=user_obj.username, password=password
                )
            except User.DoesNotExist:
                user = None

        # If authentication succeeds, log user in
        if user is not None:
            login(request, user)
            return redirect("dashboardPage")
        else:
            # Invalid credentials: show error and redirect to login
            messages.error(request, "Invalid credentials")
            return redirect("loginPage")
    else:
        # GET request: show empty login form
        form = UserAuthenticationForm()

    context = {"form": form}
    return render(request, "login.html", context)


# Register page view
@login_required(login_url="/login/")
def registerPage(request):
    """
    Handle user registration manually (without Django forms validation messages).
    - Collect first name, last name, email, phone, passwords, role.
    - Ensure passwords match.
    - Create a new user and redirect to users page.
    """
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        role = request.POST.get("role")

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        # Create the new user
        user = User.objects.create_user(
            username=f"{first_name}{last_name}".lower(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role=role,
            password=password1,
        )
        return redirect("usersPage")

    # GET request: render registration page
    return render(request, "adduser.html")


# Dashboard view
@login_required(login_url="/login/")  # redirect to login if not logged in
@never_cache
def dashboardPage(request):
    """
    Render the dashboard for the logged-in user.
    - Display metrics: total sales, daily sales, monthly sales, stock count.
    - Include charts for last 6 months sales and stock categories.
    """
    user = request.user

    # Default metrics
    total_sales = daily_sales = monthly_sales = total_stock = 0
    latest_sales = Sale.objects.order_by("-date")[:10]

    today = date.today()

    if user.role in ["MANAGER", "SALES_AGENT"]:
        total_sales = Sale.objects.count()

        # Daily sales sum
        today_sales = Sale.objects.filter(date=today)
        daily_sales = today_sales.aggregate(total=Sum("total_price"))["total"] or 0

        # Monthly sales sum
        monthly_sales = (
            Sale.objects.filter(
                date__year=today.year, date__month=today.month
            ).aggregate(total=Sum("total_price"))["total"]
            or 0
        )

        total_stock = Stock.objects.count()
        latest_sales = Sale.objects.order_by("-date")[:10]

    # Prepare monthly sales chart data (last 6 months)
    last_6_months = Sale.objects.filter(
        date__gte=date(today.year, today.month - 5 if today.month > 5 else 1, 1)
    )
    monthly_data = (
        last_6_months.annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("total_price"))
        .order_by("month")
    )
    monthly_labels = [m["month"].strftime("%b %Y") for m in monthly_data]
    monthly_sales_data = [float(m["total"] or 0) for m in monthly_data]

    # Prepare pie chart for stock categories
    category_data = (
        Stock.objects.values("category")
        .annotate(total=Sum("quantity"))
        .order_by("-total")
    )
    category_labels = [c["category"] for c in category_data]
    category_sales_data = [c["total"] for c in category_data]

    context = {
        "user": user,
        "total_sales": total_sales,
        "daily_total": daily_sales,
        "monthly_sales": monthly_sales,
        "total_stock": total_stock,
        "latest_sales": latest_sales,
        "monthly_labels": json.dumps(monthly_labels),
        "monthly_sales_data": json.dumps(monthly_sales_data),
        "category_labels": json.dumps(category_labels),
        "category_sales_data": json.dumps(category_sales_data),
    }

    return render(request, "dashboard.html", context)


# Sales page view
@login_required(login_url="/login/")
def salesPage(request):
    """
    Display all sales with pagination (10 per page).
    """
    all_sales = Sale.objects.all().order_by("-date")
    paginator = Paginator(all_sales, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "sales.html", {"page_obj": page_obj})


# Stocks page view
@login_required(login_url="/login/")
def stocksPage(request):
    """
    Display all stocks with pagination (10 per page).
    """
    all_stocks = Stock.objects.all().order_by("name")
    paginator = Paginator(all_stocks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "stocks.html", {"page_obj": page_obj})


# Record new sale view
@login_required(login_url="/login/")
def recordSales(request):
    """
    Handle creation of a new sale.
    - Validates stock before saving.
    - Displays errors on the same page (no double messages).
    """
    all_stocks = Stock.objects.all()

    if request.method == "POST":
        stock_id = request.POST.get("stock_item")
        if not stock_id:
            messages.error(request, "Please select a product.")
            return render(request, "record_sales.html", {"all_stocks": all_stocks})

        stock_item = get_object_or_404(Stock, id=stock_id)
        quantity_sold = int(request.POST.get("quantity_sold", 0))
        sale_price = Decimal(request.POST.get("sale_price", "0"))
        customer_name = request.POST.get("customer_name")
        payment_method = request.POST.get("payment_method")

        # Validate stock
        if quantity_sold > stock_item.quantity:
            messages.error(
                request,
                f"Not enough stock available for {stock_item.name}. "
                f"Available: {stock_item.quantity}, requested: {quantity_sold}.",
            )
            # Render the same form again instead of redirecting
            return render(request, "record_sales.html", {"all_stocks": all_stocks})

        # Deduct from stock and save
        stock_item.quantity -= quantity_sold
        stock_item.save()

        # Create the sale record
        Sale.objects.create(
            stock_item=stock_item,
            quantity_sold=quantity_sold,
            sale_price=sale_price,
            customer_name=customer_name,
            payment_method=payment_method,
            sales_agent=request.user,
        )

        messages.success(
            request,
            f"Sale recorded successfully! Remaining stock: {stock_item.quantity}",
        )
        return redirect("salesPage")

    return render(request, "record_sales.html", {"all_stocks": all_stocks})


# Sales report view
@login_required(login_url="/login/")
def sales_report(request):
    """
    Display daily and monthly sales reports.
    """
    all_sales = Sale.objects.all().order_by("-date")
    paginator = Paginator(all_sales, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    today = now().date()
    sales_today = Sale.objects.filter(date=today)
    monthly_sales = Sale.objects.filter(date__month=today.month, date__year=today.year)

    context = {
        "daily_total": sum(s.amount for s in sales_today),
        "monthly_total": sum(s.amount for s in monthly_sales),
        "page_obj": page_obj,
        "all_sales": all_sales,
    }
    return render(request, "salesreport.html", context)


# Record new stock view
@login_required(login_url="/login/")
def recordStocks(request):
    """
    Handle recording of new stock items.
    - Validate required fields.
    - Save stock and redirect to stocks page.
    """
    today = now().date()
    categories = [
        "Poles",
        "Hardwood",
        "Home Furniture",
        "Office Furniture",
        "Softwood",
        "Timber",
        "Garden Furniture",
    ]

    if request.method == "POST":
        # Get all fields from form
        name = request.POST.get("name")
        type_ = request.POST.get("type")
        quantity = request.POST.get("quantity")
        category = request.POST.get("category")
        color = request.POST.get("color")
        cost_price = request.POST.get("cost_price")
        selling_price = request.POST.get("selling_price")
        supplier = request.POST.get("supplier")
        date_added = parse_date(request.POST.get("date"))

        # Field validations
        if not name:
            messages.error(request, "Product name is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not type_:
            messages.error(request, "Type is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not quantity:
            messages.error(request, "Quantity is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not category:
            messages.error(request, "Category is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not color:
            messages.error(request, "Color is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not cost_price:
            messages.error(request, "Cost price is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not selling_price:
            messages.error(request, "Selling price is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not supplier:
            messages.error(request, "Supplier is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )
        if not date_added:
            messages.error(request, "Date is required.")
            return render(
                request,
                "record_stocks.html",
                {"categories": categories, **request.POST},
            )

        # Save the stock item
        stock = Stock(
            name=name,
            type=type_,
            quantity=quantity or 0,
            category=category,
            color=color,
            cost_price=cost_price or 0,
            selling_price=selling_price or 0,
            supplier=supplier,
            date_added=date_added,
        )
        stock.save()
        messages.success(request, f"Stock '{name}' added successfully!")
        return redirect("stocksPage")

    return render(request, "record_stocks.html", {"categories": categories})


# Stocks report view
@login_required(login_url="loginPage")
def stocks_report(request):
    """
    Display all stock items with pagination.
    - Calculate total stock value.
    """
    all_stocks = Stock.objects.all().order_by("name")
    paginator = Paginator(all_stocks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    total_value = sum(stock.selling_price * stock.quantity for stock in all_stocks)

    context = {"page_obj": page_obj, "total_value": total_value}
    return render(request, "stocksreport.html", context)


# View specific sale
@login_required(login_url="/login/")
def viewSales(request, sale_id):
    """
    Show details of a single sale.
    - Supports modal AJAX view if requested.
    """
    sale = Sale.objects.get(id=sale_id)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "view_sales_modal.html", {"sale": sale})
    return render(request, "viewsales.html", {"sale": sale})


# View specific stock
@login_required(login_url="/login/")
def viewStocks(request, stock_id):
    """
    Show details of a single stock item.
    """
    stock = Stock.objects.get(id=stock_id)
    return render(request, "viewstocks.html", {"stock": stock})


# Edit existing sale
@login_required(login_url="/login/")
def editSales(request, sale_id):
    """
    Edit a sale record.
    - Update stock, quantity, price, transport, and recalculate totals.
    """
    sale = Sale.objects.get(id=sale_id)
    all_stocks = Stock.objects.all()

    if request.method == "POST":
        stock_id = request.POST.get("stock_item")
        sale.stock_item = get_object_or_404(Stock, id=stock_id)
        sale.quantity_sold = int(request.POST.get("quantity_sold", 0))
        sale.sale_price = Decimal(request.POST.get("sale_price", "0"))
        sale.customer_name = request.POST.get("customer_name")
        sale.payment_method = request.POST.get("payment_method")
        sale.transport = request.POST.get("transport", "no")

        # Calculate transport cost
        if sale.transport.lower() == "yes":
            sale.transport = sale.sale_price * Decimal("0.05")
        else:
            sale.transport = Decimal("0")

        sale.sales_agent = request.user
        sale.save()
        return redirect("salesPage")

    return render(request, "editsales.html", {"sale": sale, "all_stocks": all_stocks})


# Edit stock item
@login_required(login_url="/login/")
def editStocks(request, stock_id):
    """
    Edit a stock record.
    """
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


# Delete sale
@login_required(login_url="/login/")
def deleteSales(request, sale_id):
    """
    Delete a sale record after confirmation.
    """
    sale = Sale.objects.get(id=sale_id)
    if request.method == "POST":
        sale.delete()
        return redirect("salesPage")
    return render(request, "deletesale.html", {"sale": sale})


# Delete stock
@login_required(login_url="/login/")
def deleteStocks(request, stock_id):
    """
    Delete a stock record after confirmation.
    """
    stock = Stock.objects.get(id=stock_id)
    if request.method == "POST":
        stock.delete()
        return redirect("stocksPage")
    return render(request, "deletestock.html", {"stock": stock})


# Users page
@login_required(login_url="/login/")
def usersPage(request):
    """
    Display all registered users.
    """
    users = User.objects.all()
    return render(request, "users.html", {"users": users})


# Edit user
@login_required(login_url="/login/")
def editUser(request, user_id):
    """
    Edit user profile.
    """
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.phone = request.POST.get("phone")
        user.role = request.POST.get("role")
        user.save()
        return redirect("usersPage")
    return render(request, "editUser.html", {"user": user})


# View user
@login_required(login_url="/login/")
def viewUser(request, user_id):
    """
    View user details.
    """
    user = User.objects.get(id=user_id)
    return render(request, "viewuser.html", {"user": user})


# Delete user
@login_required(login_url="/login/")
def deleteUser(request, user_id):
    """
    Delete a user after confirmation.
    """
    user = User.objects.get(id=user_id)
    if request.method == "POST":
        user.delete()
        return redirect("usersPage")
    return render(request, "deleteuser.html", {"user": user})


# Print receipt for a sale
@login_required(login_url="/login/")
def print_receipt(request, sale_id):
    """
    Prepare sale receipt data for printing.
    """
    sale = get_object_or_404(Sale, id=sale_id)
    unit_price = sale.sale_price / sale.quantity_sold  # Calculate unit price
    line_total = sale.quantity_sold * unit_price
    total_paid = line_total + (sale.transport or Decimal("0"))

    context = {
        "sale": sale,
        "unit_price": unit_price,
        "total_paid": total_paid,
    }
    return render(request, "receipt.html", context)


# Logout page
@login_required(login_url="/login/")
def logoutPage(request):
    """
    Log out the user and show logout confirmation page.
    """
    logout(request)
    return render(request, "logout.html")
