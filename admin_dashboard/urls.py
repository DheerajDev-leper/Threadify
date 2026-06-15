from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),

    # Products
    path('products/', views.product_list, name='admin_product_list'),
    path('products/add/', views.product_add, name='admin_product_add'),
    path('products/<int:pk>/edit/', views.product_edit, name='admin_product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='admin_product_delete'),

    # Variations
    path('products/<int:product_pk>/variation/add/', views.variation_add, name='admin_variation_add'),
    path('variations/<int:pk>/delete/', views.variation_delete, name='admin_variation_delete'),

    # Categories
    path('categories/', views.category_list, name='admin_category_list'),
    path('categories/add/', views.category_add, name='admin_category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='admin_category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='admin_category_delete'),

    # Orders
    path('orders/', views.order_list, name='admin_order_list'),
    path('orders/<int:pk>/', views.order_detail, name='admin_order_detail'),

    # Customers
    path('customers/', views.customer_list, name='admin_customer_list'),
    path('customers/<int:pk>/', views.customer_detail, name='admin_customer_detail'),
    path('customers/<int:pk>/toggle/', views.customer_toggle_active, name='admin_customer_toggle'),

    # Reports
    path('reports/', views.reports, name='admin_reports'),

    # Reviews
    path('reviews/', views.review_list, name='admin_review_list'),
    path('reviews/<int:pk>/toggle/', views.review_toggle, name='admin_review_toggle'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='admin_review_delete'),

    path('admin-dashboard/login/', views.admin_login, name='admin_login'),
]