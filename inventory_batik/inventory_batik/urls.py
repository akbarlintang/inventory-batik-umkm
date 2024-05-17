"""
URL configuration for inventory_batik project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls.conf import include

from inventory.views import *

app_name = 'inventory'

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('inventory/', include('inventory.urls')),

    # Dashboard
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard_view, name='dashboard'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('api/get-sales-data/', get_sales_data, name='get-sales-data'),
    path('api/get_purchase_data/', get_purchase_data, name='get_purchase_data'),
    
    # Outlet
    path('outlet/', outlet_view, name='outlet.index'),
    path('outlet/create', outlet_create_view, name='outlet.create'),
    path('outlet/update/<int:outlet_id>', outlet_update_view, name='outlet.update'),
    path('outlet/delete/<int:outlet_id>', outlet_delete_view, name='outlet.delete'),
    path('outlet/select/<outlet_id>', outlet_select_view, name='outlet.select'),
    path('outlet/get', outlet_get_view, name='outlet.get'),

    # Material
    path('material/', material_view, name='material.index'),
    path('material/create', material_create_view, name='material.create'),
    path('material/update/<int:material_id>', material_update_view, name='material.update'),
    path('material/delete/<int:material_id>', material_delete_view, name='material.delete'),

    # Product
    path('product/', product_view, name='product.index'),
    path('product/create', product_create_view, name='product.create'),
    path('product/update/<int:product_id>', product_update_view, name='product.update'),
    path('product/delete/<int:product_id>', product_delete_view, name='product.delete'),

    # Product recipe
    path('product/recipe/<int:product_id>', product_recipe_view, name='product.recipe.index'),
    path('product/recipe/create/<int:product_id>', product_recipe_create_view, name='product.recipe.create'),
    path('product/recipe/delete/<int:product_id>/<int:material_id>', product_recipe_delete_view, name='product.recipe.delete'),

    # Purchase
    path('purchase/', purchase_view, name='purchase.index'),
    path('purchase/create', purchase_create_view, name='purchase.create'),
    path('purchase/update/<int:purchase_id>', purchase_update_view, name='purchase.update'),
    path('purchase/delete/<int:purchase_id>', purchase_delete_view, name='purchase.delete'),

    # Production
    path('production/', production_view, name='production.index'),
    path('production/create', production_create_view, name='production.create'),
    path('production/update/<int:production_id>', production_update_view, name='production.update'),
    path('production/delete/<int:production_id>', production_delete_view, name='production.delete'),

    # Sales
    path('sales/', sales_view, name='sales.index'),
    path('sales/create', sales_create_view, name='sales.create'),
    path('sales/update/<int:sales_id>', sales_update_view, name='sales.update'),
    path('sales/delete/<int:sales_id>', sales_delete_view, name='sales.delete'),

    # Stocks
    path('stock/', stock_view, name='stock.index'),

    # Transaction
    path('transaction/', transaction_view, name='transaction.index'),

    # Export
    path('export/', export_view, name='export.index'),

    # Periodic Review
    path('periodic/', periodic_view, name='periodic.index'),
]
