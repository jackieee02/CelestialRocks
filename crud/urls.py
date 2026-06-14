from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('age-verify/', views.age_verify, name='age_verify'),
    path('access-denied/', views.access_denied, name='access_denied'),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('about/', views.about, name='about'),
    path('order-status/', views.order_status, name='order_status'),
    path('menu/', views.menu, name='menu'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:drink_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:drink_id>/<str:action>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:drink_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('select-seat/', views.select_seat, name='select_seat'),
    path('checkout/', views.checkout, name='checkout'),
    path('bartender/dashboard/', views.bartender_dashboard, name='bartender_dashboard'),
    path('bartender/profile/', views.bartender_profile, name='bartender_profile'),
    path('bartender/profile/edit/', views.bartender_edit_profile, name='bartender_edit_profile'),
    path('bartender/seats/', views.bartender_seats, name='bartender_seats'),
    path('bartender/orders/', views.bartender_orders, name='bartender_orders'),

    path('bartender/order/update/<int:order_id>/<str:status>/', views.update_order_status, name='update_order_status'),
    path('bartender/payment/toggle/<int:order_id>/', views.toggle_payment_status, name='toggle_payment_status'),
    path('bartender/inventory/', views.bartender_inventory, name='bartender_inventory'),
    path('bartender/proposals/', views.drink_proposals, name='drink_proposals'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/menu/', views.manage_menu, name='manage_menu'),
    path('admin/menu/add/', views.add_drink, name='add_drink'),
    path('admin/menu/edit/<int:drink_id>/', views.edit_drink, name='edit_drink'),
    path('admin/menu/delete/<int:drink_id>/', views.delete_drink, name='delete_drink'),
    path('admin/categories/', views.manage_categories, name='manage_categories'),
    path('admin/categories/add/', views.add_category, name='add_category'),
    path('admin/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('admin/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('admin/inventory/', views.manage_inventory, name='manage_inventory'),
    path('admin/inventory/add/', views.add_ingredient, name='add_ingredient'),
    path('admin/inventory/edit/<int:ingredient_id>/', views.edit_ingredient, name='edit_ingredient'),
    path('admin/inventory/delete/<int:ingredient_id>/', views.delete_ingredient, name='delete_ingredient'),
    path('admin/seats/', views.seat_designer, name='manage_seats'),
    path('admin/seats/designer/', views.seat_designer, name='seat_designer'),
    path('admin/seats/update-pos/<int:seat_id>/', views.update_seat_position, name='update_seat_position'),
    path('admin/seats/add/', views.add_seat, name='add_seat'),
    path('admin/seats/edit/<int:seat_id>/', views.edit_seat, name='edit_seat'),
    path('admin/seats/delete/<int:seat_id>/', views.delete_seat, name='delete_seat'),

    path('admin/orders/', views.admin_orders, name='admin_orders'),
    path('admin/sales-report/', views.admin_sales_report, name='admin_sales_report'),
    path('admin/proposals/', views.admin_review_proposals, name='admin_review_proposals'),
    path('admin/proposals/update/<int:proposal_id>/<str:status>/', views.update_proposal_status, name='update_proposal_status'),
    path('admin/bartenders/', views.manage_bartenders, name='manage_bartenders'),
    path('admin/bartenders/edit/<int:user_id>/', views.edit_bartender, name='edit_bartender'),
    path('admin/bartenders/delete/<int:user_id>/', views.delete_bartender, name='delete_bartender'),
    path('admin/customers/', views.manage_customers, name='manage_customers'),
    path('admin/customers/toggle-ban/<int:user_id>/', views.toggle_ban_customer, name='toggle_ban_customer'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
