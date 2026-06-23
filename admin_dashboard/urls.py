from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ─────────────────────────────────────────────────────────
    path('login/',                          views.admin_login,             name='admin_login'),
    path('logout/',                         views.admin_logout,            name='admin_logout'),
    path('register/',                       views.shop_register,           name='shop_register'),
    path('forgot-password/',                views.admin_forgot_password,   name='admin_forgot_password'),
    path('reset/<uidb64>/<token>/',         views.admin_reset_password,    name='admin_reset_password'),

    # ── Dashboard ────────────────────────────────────────────────────
    path('',                                views.admin_dashboard,      name='admin_dashboard'),
    path('reports/',                        views.reports,              name='admin_reports'),

    # ── Products ─────────────────────────────────────────────────────
    path('products/',                       views.product_list,         name='admin_product_list'),
    path('products/add/',                   views.product_add,          name='admin_product_add'),
    path('products/<int:pk>/edit/',         views.product_edit,         name='admin_product_edit'),
    path('products/<int:pk>/delete/',       views.product_delete,       name='admin_product_delete'),
    

    # ── Variants ─────────────────────────────────────────────────────
    path('products/<int:product_pk>/variants/add/',     views.variant_add,    name='admin_variant_add'),
    path('variants/<int:pk>/edit/',                      views.variant_edit,   name='admin_variant_edit'),
    path('variants/<int:pk>/delete/',                    views.variant_delete, name='admin_variant_delete'),

    # ── Gallery ──────────────────────────────────────────────────────
    path('products/<int:product_pk>/gallery/add/',      views.gallery_add,    name='admin_gallery_add'),
    path('gallery/<int:pk>/delete/',                    views.gallery_delete, name='admin_gallery_delete'),
    path('gallery/<int:pk>/color/', views.admin_gallery_color, name='admin_gallery_color'),

    # ── Categories (super admin only) ────────────────────────────────
    path('categories/',                     views.category_list,        name='admin_category_list'),
    path('categories/add/',                 views.category_add,         name='admin_category_add'),
    path('categories/<int:pk>/edit/',       views.category_edit,        name='admin_category_edit'),
    path('categories/<int:pk>/delete/',     views.category_delete,      name='admin_category_delete'),

    # ── Orders ───────────────────────────────────────────────────────
    path('orders/',                         views.order_list,           name='admin_order_list'),
    path('orders/<int:pk>/',                views.order_detail,         name='admin_order_detail'),

    # ── Customers (super admin only) ─────────────────────────────────
    path('customers/',                      views.customer_list,        name='admin_customer_list'),
    path('customers/<int:pk>/',             views.customer_detail,      name='admin_customer_detail'),
    path('customers/<int:pk>/toggle/',      views.customer_toggle,      name='admin_customer_toggle'),

    # ── Shop Owners (super admin only) ───────────────────────────────
    path('shop-owners/',                    views.shop_owner_list,      name='admin_shop_owner_list'),
    path('shop-owners/<int:pk>/approve/',   views.shop_approve,         name='admin_shop_approve'),
    path('shop-owners/<int:pk>/reject/',    views.shop_reject,          name='admin_shop_reject'),

    # ── Reviews ──────────────────────────────────────────────────────
    path('reviews/',                        views.review_list,          name='admin_review_list'),
    path('reviews/<int:pk>/toggle/',        views.review_toggle,        name='admin_review_toggle'),
    path('reviews/<int:pk>/delete/',        views.review_delete,        name='admin_review_delete'),
]