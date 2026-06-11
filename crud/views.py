from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import User, Drink, Category, Order, OrderItem, Seat, SeatReservation, Ingredient, DrinkProposal, CashPayment
from .forms import BartenderForm, DrinkForm, CategoryForm, IngredientForm, SeatForm, CustomSignupForm, DrinkProposalForm, BartenderProfileForm, EditBartenderForm
from django.utils import timezone
from django.db import models
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from datetime import datetime, timedelta
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def age_verify(request):
    if request.method == 'POST':
        # Check if the button submitted was 'yes'
        if request.POST.get('action') == 'yes':
            request.session['is_of_age'] = True
            return redirect('home')
    return render(request, 'customer/age_verify.html')

def access_denied(request):
    return render(request, 'customer/access_denied.html')

def home(request):
    return render(request, 'customer/home.html')

def menu(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', 'all')
    sort = request.GET.get('sort', 'featured')

    categories = Category.objects.all().order_by('name')
    drinks = Drink.objects.select_related('category').all()

    if query:
        drinks = drinks.filter(name__icontains=query)

    if category_id and category_id != 'all':
        drinks = drinks.filter(category_id=category_id)

    if sort == 'price_asc':
        drinks = drinks.order_by('price', 'name')
    elif sort == 'price_desc':
        drinks = drinks.order_by('-price', 'name')
    elif sort == 'name_asc':
        drinks = drinks.order_by('name')
    else:
        drinks = drinks.order_by('category__name', 'name')

    featured_drinks = list(Drink.objects.select_related('category').order_by('-id')[:6])
    recommended_drinks = list(Drink.objects.select_related('category').order_by('-id')[:4])

    cart = request.session.get('cart', {})
    cart_item_count = sum(cart.values())
    cart_total = 0
    if cart:
        for drink_id, quantity in cart.items():
            drink = Drink.objects.filter(id=drink_id).first()
            if drink:
                cart_total += float(drink.price) * quantity

    return render(request, 'customer/menu.html', {
        'categories': categories,
        'drinks': drinks,
        'featured_drinks': featured_drinks,
        'recommended_drinks': recommended_drinks,
        'query': query,
        'selected_category': category_id,
        'sort': sort,
        'cart_item_count': cart_item_count,
        'cart_total': cart_total,
    })

def add_to_cart(request, drink_id):
    cart = request.session.get('cart', {})
    drink_id_str = str(drink_id)
    cart[drink_id_str] = cart.get(drink_id_str, 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

@login_required
def update_cart_item(request, drink_id, action):
    cart = request.session.get('cart', {})
    drink_id_str = str(drink_id)
    if drink_id_str in cart:
        if action == 'add':
            cart[drink_id_str] += 1
        elif action == 'remove':
            cart[drink_id_str] -= 1
            if cart[drink_id_str] <= 0:
                del cart[drink_id_str]
    request.session['cart'] = cart
    return redirect('cart')

@login_required
def remove_from_cart(request, drink_id):
    cart = request.session.get('cart', {})
    drink_id_str = str(drink_id)
    if drink_id_str in cart:
        del cart[drink_id_str]
    request.session['cart'] = cart
    return redirect('cart')

def cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    total_items = 0
    for drink_id, quantity in cart.items():
        drink = get_object_or_404(Drink, id=drink_id)
        subtotal = drink.price * quantity
        total_price += subtotal
        total_items += quantity
        cart_items.append({'drink': drink, 'quantity': quantity, 'subtotal': subtotal})
    return render(request, 'customer/cart.html', {'cart_items': cart_items, 'total_price': total_price, 'total_items': total_items})

@login_required
def select_seat(request):
    if request.user.role != 'customer': return redirect('home')
    if request.method == 'POST':
        seat_id = request.POST.get('seat_id')
        # Validate if seat is available (excluding the current user's own reservations)
        if SeatReservation.objects.filter(seat_id=seat_id, reservation_date=timezone.now().date()).exclude(customer=request.user).exists():
            messages.error(request, "This seat has just been taken.")
            return redirect('select_seat')
        
        request.session['selected_seat'] = seat_id
        return redirect('checkout')
    
    today = timezone.now().date()
    # Find seats reserved by OTHERS today
    occupied_ids = SeatReservation.objects.filter(reservation_date=today).exclude(customer=request.user).values_list('seat_id', flat=True)
    all_seats = Seat.objects.filter(is_active=True)
    
    # Add status to seat objects
    for seat in all_seats:
        seat.is_occupied = seat.id in occupied_ids
    
    return render(request, 'customer/select_seat.html', {'seats': all_seats})

@login_required
def checkout(request):
    seat_id = request.session.get('selected_seat')
    if not seat_id:
        return redirect('select_seat')
    
    cart = request.session.get('cart', {})
    seat = get_object_or_404(Seat, id=seat_id)
    cart_items = []
    total_price = 0
    for drink_id, quantity in cart.items():
        drink = get_object_or_404(Drink, id=drink_id)
        subtotal = drink.price * quantity
        total_price += subtotal
        cart_items.append({'drink': drink, 'quantity': quantity, 'subtotal': subtotal})
    
    if request.method == 'POST':
        # Create Reservation
        reservation = SeatReservation.objects.create(
            customer=request.user,
            seat=seat,
            reservation_date=timezone.now().date()
        )
        
        # Create Order
        order = Order.objects.create(
            customer=request.user,
            seat_reservation=reservation,
            total_price=total_price
        )
        
        # Create Order Items
        for item in cart_items:
            OrderItem.objects.create(order=order, drink=item['drink'], quantity=item['quantity'])
            
        # Create Payment
        CashPayment.objects.create(order=order, amount=total_price)
            
        # Clear Session
        del request.session['cart']
        del request.session['selected_seat']
        
        return redirect('home') # Or order status page
        
    return render(request, 'customer/checkout.html', {
        'seat': seat,
        'cart_items': cart_items,
        'total_price': total_price
    })

@login_required
def bartender_dashboard(request):
    if request.user.role != 'bartender':
        return redirect('home')
    
    today = timezone.now().date()
    stats_list = [
        {'label': 'Active Orders', 'value': Order.objects.filter(status__in=['pending', 'preparing']).count(), 'color': 'white'},
        {'label': 'Occupied Seats', 'value': SeatReservation.objects.filter(reservation_date=today).count(), 'color': 'purple'},
        {'label': 'Pending Payments', 'value': CashPayment.objects.filter(status='pending').count(), 'color': 'yellow'},
        {'label': 'Low Stock', 'value': Ingredient.objects.filter(stock_level__lt=models.F('low_stock_threshold')).count(), 'color': 'red'},
    ]
    
    pending_orders = Order.objects.filter(status='pending')
    preparing_orders = Order.objects.filter(status='preparing')
    pending_payments = CashPayment.objects.filter(status='pending')
    
    return render(request, 'bartender/dashboard.html', {
        'stats_list': stats_list,
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'pending_payments': pending_payments
    })

@login_required
def bartender_orders(request):
    if request.user.role != 'bartender': return redirect('home')
    orders = Order.objects.all().order_by('-created_at')
    
    board_columns = [
        ('Pending', 'pending', 'yellow'),
        ('Preparing', 'preparing', 'purple'),
        ('Ready', 'completed', 'green'),
        ('Cancelled', 'cancelled', 'red'),
    ]
    
    status_counts = {
        'pending': Order.objects.filter(status='pending').count(),
        'preparing': Order.objects.filter(status='preparing').count(),
        'completed': Order.objects.filter(status='completed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    context = {
        'orders': orders,
        'board_columns': board_columns,
        'status_counts': status_counts,
        'active_count': Order.objects.filter(status__in=['pending', 'preparing']).count(),
        'pending_count': status_counts['pending']
    }
    return render(request, 'bartender/orders.html', context)

@login_required
def update_order_status(request, order_id, status):
    if request.user.role != 'bartender':
        return redirect('home')
    order = get_object_or_404(Order, id=order_id)
    order.status = status
    order.save()
    return redirect('bartender_orders')

@login_required
def bartender_inventory(request):
    if request.user.role != 'bartender':
        return redirect('home')
    ingredients = Ingredient.objects.all()
    return render(request, 'bartender/inventory.html', {'ingredients': ingredients})

@login_required
def drink_proposals(request):
    if request.user.role != 'bartender': return redirect('home')
    proposals = DrinkProposal.objects.filter(bartender=request.user)
    
    stats = [
        {'label': 'Submitted', 'value': proposals.count()},
        {'label': 'Approved', 'value': proposals.filter(status='approved').count()},
        {'label': 'Pending', 'value': proposals.filter(status='pending').count()},
        {'label': 'Rejected', 'value': proposals.filter(status='rejected').count()},
    ]
    
    if request.method == 'POST':
        form = DrinkProposalForm(request.POST, request.FILES)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.bartender = request.user
            proposal.save()
            return redirect('drink_proposals')
    else:
        form = DrinkProposalForm()
    return render(request, 'bartender/proposals.html', {'proposals': proposals, 'form': form, 'stats': stats})

@login_required
def bartender_profile(request):
    if request.user.role != 'bartender': return redirect('home')
    
    # Calculate stats for the bartender
    all_orders = Order.objects.all()
    completed_orders = all_orders.filter(status='completed')
    
    orders_served = completed_orders.count()
    shift_orders = Order.objects.filter(status__in=['pending', 'preparing', 'completed'], created_at__date=timezone.now().date()).count()
    assigned_customers = Order.objects.filter(status__in=['pending', 'preparing']).values('customer').distinct().count()
    
    # Performance calculation: % of completed orders out of total orders handled
    total_handled = all_orders.count()
    performance = (completed_orders.count() / total_handled * 100) if total_handled > 0 else 0
    
    stats = {
        'orders_served': orders_served,
        'shift_orders': shift_orders,
        'assigned_customers': assigned_customers,
        'performance': round(performance),
    }
    
    return render(request, 'bartender/profile.html', {'stats': stats})

@login_required
def bartender_edit_profile(request):
    if request.user.role != 'bartender': return redirect('home')
    if request.method == 'POST':
        form = BartenderProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('bartender_profile')
    else:
        form = BartenderProfileForm(instance=request.user)
    return render(request, 'bartender/edit_profile.html', {'form': form})

@login_required
def bartender_seats(request):
    if request.user.role != 'bartender': return redirect('home')
    today = timezone.now().date()
    occupied_ids = SeatReservation.objects.filter(reservation_date=today).values_list('seat_id', flat=True)
    all_seats = Seat.objects.filter(is_active=True)
    for seat in all_seats:
        seat.is_occupied = seat.id in occupied_ids
    return render(request, 'bartender/seats.html', {'seats': all_seats})

@login_required
def toggle_payment_status(request, order_id):
    if request.user.role != 'bartender': return redirect('home')
    payment = get_object_or_404(CashPayment, order_id=order_id)
    payment.status = 'paid' if payment.status == 'pending' else 'pending'
    payment.save()
    messages.success(request, f"Payment status for Order {order_id} updated.")
    return redirect('bartender_orders')

@login_required
def admin_review_proposals(request):
    if request.user.role != 'admin': return redirect('home')
    proposals = DrinkProposal.objects.filter(status='pending')
    return render(request, 'admin/manage_proposals.html', {'proposals': proposals})

@login_required
def update_proposal_status(request, proposal_id, status):
    if request.user.role != 'admin': return redirect('home')
    proposal = get_object_or_404(DrinkProposal, id=proposal_id)
    proposal.status = status
    proposal.save()
    if status == 'approved':
        # Automatically add to menu
        Drink.objects.create(
            name=proposal.name,
            category=Category.objects.first(), # Default category
            price=proposal.suggested_price
        )
    return redirect('admin_review_proposals')

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    # Analytics data
    today = timezone.now().date()
    available_seats = Seat.objects.filter(is_active=True).count() - SeatReservation.objects.filter(reservation_date=today).count()
    total_customers = User.objects.filter(role='customer').count()
    daily_sales = Order.objects.filter(status='completed', created_at__date=today).aggregate(models.Sum('total_price'))['total_price__sum'] or 0
    total_orders_today = Order.objects.filter(created_at__date=today).count()
    low_stock_ingredients = Ingredient.objects.filter(stock_level__lt=models.F('low_stock_threshold'))
    
    # Chart data (past 7 days)
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = today - timezone.timedelta(days=i)
        chart_labels.append(day.strftime('%a'))
        revenue = Order.objects.filter(status='completed', created_at__date=day).aggregate(models.Sum('total_price'))['total_price__sum'] or 0
        chart_data.append(float(revenue))

    quick_actions = [
        {'title': 'Manage Menu', 'url': 'manage_menu', 'icon': '🍹'},
        {'title': 'Manage Inventory', 'url': 'manage_inventory', 'icon': '📦'},
        {'title': 'Manage Seats', 'url': 'manage_seats', 'icon': '🪑'},
        {'title': 'Manage Orders', 'url': 'admin_orders', 'icon': '🛒'},
        {'title': 'Sales Reports', 'url': 'admin_sales_report', 'icon': '📈'},
        {'title': 'Manage Users', 'url': 'manage_customers', 'icon': '👥'},
    ]
    
    context = {
        'available_seats': available_seats,
        'total_customers': total_customers,
        'daily_sales': daily_sales,
        'total_orders_today': total_orders_today,
        'low_stock_ingredients': low_stock_ingredients,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'quick_actions': quick_actions,
    }
    return render(request, 'admin/dashboard.html', context)

# --- Admin Menu Management ---
@login_required
def manage_menu(request):
    if request.user.role != 'admin': return redirect('home')
    query = request.GET.get('q')
    drinks = Drink.objects.select_related('category').all()
    categories = Category.objects.all()
    if query:
        drinks = drinks.filter(name__icontains=query)
    
    stats = {
        'total_drinks': drinks.count(),
        'total_categories': categories.count(),
        'available_drinks': drinks.count(), # Simplify for prototype
        'avg_price': drinks.aggregate(models.Avg('price'))['price__avg'] or 0
    }
    
    return render(request, 'admin/manage_menu.html', {
        'drinks': drinks, 
        'categories': categories, 
        'query': query,
        'stats': stats
    })

@login_required
def add_drink(request):
    if request.user.role != 'admin': return redirect('home')
    if request.method == 'POST':
        form = DrinkForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Drink successfully added to the menu!")
            return redirect('manage_menu')
    else:
        form = DrinkForm()
    return render(request, 'admin/add_drink.html', {'form': form})

@login_required
def manage_categories(request):
    if request.user.role != 'admin': return redirect('home')
    categories = Category.objects.all()
    return render(request, 'admin/manage_categories.html', {'categories': categories})

@login_required
def add_category(request):
    if request.user.role != 'admin': return redirect('home')
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    return render(request, 'admin/add_category.html', {'form': form})

# --- Admin Inventory Management ---
@login_required
def manage_inventory(request):
    if request.user.role != 'admin': return redirect('home')
    query = request.GET.get('q')
    ingredients = Ingredient.objects.all()
    if query:
        ingredients = ingredients.filter(name__icontains=query)
        
    stats = {
        'total': ingredients.count(),
        'healthy': ingredients.filter(stock_level__gte=models.F('low_stock_threshold') + 5).count(),
        'low': ingredients.filter(stock_level__gte=models.F('low_stock_threshold'), stock_level__lt=models.F('low_stock_threshold') + 5).count(),
        'critical': ingredients.filter(stock_level__lt=models.F('low_stock_threshold')).count(),
    }
    
    return render(request, 'admin/manage_inventory.html', {'ingredients': ingredients, 'query': query, 'stats': stats})

@login_required
def add_ingredient(request):
    if request.user.role != 'admin': return redirect('home')
    if request.method == 'POST':
        form = IngredientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_inventory')
    else:
        form = IngredientForm()
    return render(request, 'admin/add_ingredient.html', {'form': form})

# --- Admin Seat Management ---
@login_required
def seat_designer(request):
    if request.user.role != 'admin': return redirect('home')
    today = timezone.now().date()
    occupied_ids = SeatReservation.objects.filter(reservation_date=today).values_list('seat_id', flat=True)
    seats = Seat.objects.all()
    
    for seat in seats:
        seat.is_occupied = seat.id in occupied_ids
    
    return render(request, 'admin/seat_designer.html', {'seats': seats})

@login_required
@csrf_exempt
def update_seat_position(request, seat_id):
    if request.user.role != 'admin': return JsonResponse({'status': 'error'}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        seat = get_object_or_404(Seat, id=seat_id)
        seat.x_coord = data['x']
        seat.y_coord = data['y']
        seat.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_seat(request):
    if request.user.role != 'admin': return redirect('home')
    if request.method == 'POST':
        form = SeatForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_seats')
    else:
        form = SeatForm()
    return render(request, 'admin/add_seat.html', {'form': form})

# --- Admin Edit/Delete Views ---
@login_required
def edit_drink(request, drink_id):
    if request.user.role != 'admin': return redirect('home')
    drink = get_object_or_404(Drink, id=drink_id)
    if request.method == 'POST':
        form = DrinkForm(request.POST, request.FILES, instance=drink)
        if form.is_valid():
            form.save()
            return redirect('manage_menu')
    else:
        form = DrinkForm(instance=drink)
    return render(request, 'admin/edit_drink.html', {'form': form, 'drink': drink})

@login_required
def delete_drink(request, drink_id):
    if request.user.role != 'admin': return redirect('home')
    drink = get_object_or_404(Drink, id=drink_id)
    if request.method == 'POST':
        drink.delete()
        return redirect('manage_menu')
    return render(request, 'admin/confirm_delete.html', {'object': drink})

@login_required
def edit_category(request, category_id):
    if request.user.role != 'admin': return redirect('home')
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('manage_menu')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'admin/edit_category.html', {'form': form})

@login_required
def delete_category(request, category_id):
    if request.user.role != 'admin': return redirect('home')
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('manage_menu')
    return render(request, 'admin/confirm_delete.html', {'object': category})

@login_required
def edit_ingredient(request, ingredient_id):
    if request.user.role != 'admin': return redirect('home')
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == 'POST':
        form = IngredientForm(request.POST, request.FILES, instance=ingredient)
        if form.is_valid():
            form.save()
            return redirect('manage_inventory')
    else:
        form = IngredientForm(instance=ingredient)
    return render(request, 'admin/edit_ingredient.html', {'form': form, 'object': ingredient})

@login_required
def delete_ingredient(request, ingredient_id):
    if request.user.role != 'admin': return redirect('home')
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == 'POST':
        ingredient.delete()
        return redirect('manage_inventory')
    return render(request, 'admin/confirm_delete.html', {'object': ingredient})

@login_required
def edit_seat(request, seat_id):
    if request.user.role != 'admin': return redirect('home')
    seat = get_object_or_404(Seat, id=seat_id)
    if request.method == 'POST':
        form = SeatForm(request.POST, instance=seat)
        if form.is_valid():
            form.save()
            return redirect('manage_seats')
    else:
        form = SeatForm(instance=seat)
    return render(request, 'admin/edit_seat.html', {'form': form, 'title': 'Edit Seat'})

@login_required
def delete_seat(request, seat_id):
    if request.user.role != 'admin': return redirect('home')
    seat = get_object_or_404(Seat, id=seat_id)
    if request.method == 'POST':
        seat.delete()
        return redirect('manage_seats')
    return render(request, 'admin/confirm_delete.html', {'object': seat})

@login_required
def edit_bartender(request, user_id):
    if request.user.role != 'admin': return redirect('home')
    bartender = get_object_or_404(User, id=user_id, role='bartender')
    
    # Calculate performance stats (placeholder logic)
    stats = {
        'orders_completed': Order.objects.filter(status='completed').count(),
        'performance': 92,
    }
    
    if request.method == 'POST':
        form = EditBartenderForm(request.POST, instance=bartender)
        if form.is_valid():
            form.save()
            return redirect('manage_bartenders')
    else:
        form = EditBartenderForm(instance=bartender)
    return render(request, 'admin/edit_bartender.html', {'form': form, 'bartender': bartender, 'stats': stats})

@login_required
def delete_bartender(request, user_id):
    if request.user.role != 'admin': return redirect('home')
    user = get_object_or_404(User, id=user_id, role='bartender')
    if request.method == 'POST':
        user.delete()
        return redirect('manage_bartenders')
    return render(request, 'admin/confirm_delete.html', {'object': user})

# --- Admin Order & Sales Management ---
@login_required
def admin_orders(request):
    if request.user.role != 'admin': return redirect('home')
    orders = Order.objects.select_related('customer', 'seat_reservation').all()
    return render(request, 'admin/manage_orders.html', {'orders': orders})

@login_required
def admin_sales_report(request):
    if request.user.role != 'admin': return redirect('home')
    
    filter_type = request.GET.get('filter', 'day')
    date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

    orders = Order.objects.filter(status='completed')
    
    if filter_type == 'day':
        orders = orders.filter(created_at__date=date_obj)
    elif filter_type == 'week':
        # Simple week filtering
        import datetime as dt
        start_date = date_obj - dt.timedelta(days=date_obj.weekday())
        end_date = start_date + dt.timedelta(days=6)
        orders = orders.filter(created_at__date__range=[start_date, end_date])
    elif filter_type == 'month':
        orders = orders.filter(created_at__year=date_obj.year, created_at__month=date_obj.month)

    total_orders = orders.count()
    total_revenue = orders.aggregate(models.Sum('total_price'))['total_price__sum'] or 0

    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = date_obj - timedelta(days=i)
        chart_labels.append(day.strftime('%b %d'))
        day_orders = Order.objects.filter(status='completed', created_at__date=day)
        day_revenue = day_orders.aggregate(models.Sum('total_price'))['total_price__sum'] or 0
        chart_data.append(float(day_revenue))
    
    return render(request, 'admin/sales_report.html', {
        'total_orders': total_orders, 
        'total_revenue': total_revenue,
        'filter_type': filter_type,
        'date': date_str,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })

@login_required
def manage_bartenders(request):
    if request.user.role != 'admin':
        return redirect('home')
    query = request.GET.get('q')
    bartenders = User.objects.filter(role='bartender')
    if query:
        bartenders = bartenders.filter(username__icontains=query)
    if request.method == 'POST':
        form = BartenderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_bartenders')
    else:
        form = BartenderForm()
    return render(request, 'admin/manage_bartenders.html', {'bartenders': bartenders, 'form': form, 'query': query})

@login_required
def manage_customers(request):
    if request.user.role != 'admin':
        return redirect('home')
    query = request.GET.get('q')
    customers = User.objects.filter(role='customer')
    if query:
        customers = customers.filter(username__icontains=query)
    return render(request, 'admin/manage_customers.html', {'customers': customers, 'query': query})

@login_required
def toggle_ban_customer(request, user_id):
    if request.user.role != 'admin':
        return redirect('home')
    user = get_object_or_404(User, id=user_id, role='customer')
    user.is_banned = not user.is_banned
    user.save()
    return redirect('manage_customers')

# --- Customer Authentication & Pages ---
def signup(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomSignupForm()
    return render(request, 'customer/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_banned:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Your account is banned.")
    else:
        form = AuthenticationForm()
    return render(request, 'customer/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def about(request):
    return render(request, 'customer/about.html')

@login_required
def order_status(request):
    if request.user.role != 'customer': return redirect('home')
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    stats = {
        'total_orders': orders.count(),
        'total_spent': orders.filter(status='completed').aggregate(models.Sum('total_price'))['total_price__sum'] or 0,
        'total_drinks': orders.aggregate(models.Sum('items__quantity'))['items__quantity__sum'] or 0,
        'total_seats': orders.values('seat_reservation__seat').distinct().count(),
    }
    
    return render(request, 'customer/order_status.html', {'orders': orders, 'stats': stats})
