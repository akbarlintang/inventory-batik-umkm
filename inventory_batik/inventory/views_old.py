from __future__ import division

from django.http import Http404
from django.contrib import messages
from django.http import HttpResponse
from django.core import serializers
import json
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
# from decorators import anonymous_required
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Min, Max
from django.db.models.functions import TruncDate

from collections import defaultdict
from datetime import timedelta

from .models import *

from .forms import *

# import dependency pso dan periodic review
import pandas as pd
import csv
import numpy as np
import random
import math
from statistics import NormalDist
from scipy.stats import norm
from statistics import stdev
import io, base64
import seaborn as sns
from matplotlib import pyplot as plt
import random
from scipy.integrate import quad
from matplotlib.ticker import FuncFormatter
from datetime import datetime
import time

from skopt import gp_minimize
from skopt.space import Integer, Real
from skopt.utils import use_named_args

# Map each field prefix to its variabel code
VARIABEL_MAP = {
    'PEOU': 'PEOU',
    'PU':   'PU',
    'CONF': 'CONF',
    'ATT':  'ATT',
    'TRST': 'TRST',
    'SAT':  'SAT',
    'CI':   'CI',
}

JAWABAN_CODES = [
    'PEOU_1', 'PEOU_2', 'PEOU_3', 'PEOU_4', 'PEOU_5',
    'PU_1',   'PU_2',   'PU_3',   'PU_4',
    'CONF_1', 'CONF_2', 'CONF_3',
    'ATT_1',  'ATT_2',  'ATT_3',
    'TRST_1', 'TRST_2', 'TRST_3',
    'SAT_1',  'SAT_2',  'SAT_3',
    'CI_1',   'CI_2',   'CI_3',
]

def anonymous_required(view_function):
    def wrapper_function(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        else:
            return view_function(request, *args, **kwargs)
    return wrapper_function


@anonymous_required

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email    = request.POST['email']

        if len(username) < 1:
            return render(request, 'auth/register.html', {'error': 'Username is required!'})

        if len(email) < 1:
            return render(request, 'auth/register.html', {'error': 'Email is required!'})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'auth/register.html', {'error': 'Username already exists'})

        # Check if password meets minimum length requirement
        if len(password) < 8:
            return render(request, 'auth/register.html', {'error': 'Password must be at least 8 characters'})
        
        # Hash password
        hashed_password = make_password(password)

        # Create user with hashed password
        user = User.objects.create(username=username, password=hashed_password)
        user.save()

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'auth/register.html', {'error': 'Failed to register user'})
    else:
        return render(request, 'auth/register.html')

@anonymous_required
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, 'auth/login.html', {'error': 'Username tidak ditemukan'})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'auth/login.html', {'error': 'Password salah'})
    else:
        return render(request, 'auth/login.html')

# Dashboard
@login_required
def dashboard_view(request):
    user_id         = request.user.id
    purchases       = Purchase.objects.filter(user_id=user_id)
    sales           = Sales.objects.filter(user_id=user_id)
    products        = Item.objects.filter(type="JADI", user_id=user_id)
    outlets         = Outlet.objects.filter(user_id=user_id)

    purchase_total  = 0
    for p in purchases:
        purchase_total += int(p.price) * int(p.amount)

    sales_total     = 0
    for s in sales:
        sales_total += int(s.price) * int(s.amount)

    product_list = []
    for prod in products:
        product_list.append(prod.name)
    
    context = {
        "purchases"     : purchase_total,
        "sales"         : sales_total,
        "products"      : products,
        "outlets"       : outlets,
        "product_list"  : product_list
    }

    return render(request, 'dashboard/index.html', context)

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

def get_sales_data(request):
    user_id         = request.user.id
    # Ambil tanggal awal bulan ini
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Ambil tanggal awal bulan berikutnya
    start_of_next_month = (start_of_month + timedelta(days=32)).replace(day=1)

    # Filter data penjualan hanya untuk bulan ini
    sales = Sales.objects.filter(created_at__gte=start_of_month, created_at__lt=start_of_next_month, user_id=user_id)

    item_sales_count = {}

    for sale in sales:
        item_id = sale.item_id
        item_name = sale.item.name  # Sesuaikan dengan struktur model Anda
        item_sales_count[item_name] = item_sales_count.get(item_name, 0) + int(sale.amount)

    data = {'item_names': list(item_sales_count.keys()), 'sales_counts': list(item_sales_count.values())}
    return JsonResponse(data)

def get_purchase_data(request):
    # Ambil tanggal awal bulan ini
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Ambil tanggal awal bulan berikutnya
    start_of_next_month = (start_of_month + timedelta(days=32)).replace(day=1)

    # Filter data pembelian hanya untuk bulan ini
    purchases = Purchase.objects.filter(created_at__gte=start_of_month, created_at__lt=start_of_next_month)

    # Hitung jumlah pembelian per item
    purchase_counts = purchases.values('item__name').annotate(count=Count('item'))

    data = {'purchase_data': list(purchase_counts)}
    return JsonResponse(data)

# Outlet
@login_required
def outlet_view(request):
    user_id         = request.user.id
    outlets         = Outlet.objects.filter(user_id=user_id)
    context = {
        'outlets': outlets
    }

    return render(request, 'outlet/index.html', context)

@login_required
def outlet_create_view(request):
    user_id         = request.user.id
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    if request.method == 'POST':
       # membuat objek dari class OutletForm
        form = OutletForm(request.POST)
        # Mengecek validasi form
        if form.is_valid():
            # Buat objek outlet baru dari form tanpa menyimpan ke database dulu
            new_outlet = form.save(commit=False)
            # Tambahkan user_id dari pengguna yang sedang terautentikasi
            new_outlet.user_id = user_id
            # Simpan objek outlet baru ke database
            new_outlet.save()
            # mengeset pesan sukses dan redirect ke halaman daftar task
            messages.success(request, 'Sukses Menambah Outlet baru.')
            return redirect('outlet.index')
    # Jika method-nya bukan POST
    else:
        # membuat objek dari class TaskForm
        form = OutletForm()
    # merender template form dengan memparsing data form
    return render(request, 'outlet/form.html', {'form': form})

@login_required
def outlet_update_view(request, outlet_id):
    try:
        # mengambil data outlet yang akan diubah berdasarkan outlet id
        outlet = Outlet.objects.get(pk=outlet_id)
    except Outlet.DoesNotExist:
        # Jika data outlet tidak ditemukan,
        # maka akan di redirect ke halaman 404 (Page not found).
        raise Http404("Outlet tidak ditemukan.")
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    if request.method == 'POST':
        form = OutletForm(request.POST, instance=outlet)
        if form.is_valid():
            # Simpan perubahan data ke dalam table outlets
            form.save()
            # mengeset pesan sukses dan redirect ke halaman daftar outlet
            messages.success(request, 'Sukses Mengubah Outlet.')
            return redirect('outlet.index')
    # Jika method-nya bukan POST
    else:
        # membuat objek dari class OutletForm
        form = OutletForm(instance=outlet)
    # merender template form dengan memparsing data form
    return render(request, 'outlet/form.html', {'form': form})

@login_required
def outlet_delete_view(request, outlet_id):
    try:
        # mengambil data outlet yang akan dihapus berdasarkan outlet id
        outlet = Outlet.objects.get(pk=outlet_id)
        # menghapus data dari table outlets
        outlet.delete()
        # mengeset pesan sukses dan redirect ke halaman daftar outlet
        messages.success(request, 'Sukses Menghapus Outlet.')
        return redirect('outlet.index')
    except Outlet.DoesNotExist:
        # Jika data outlet tidak ditemukan,
        # maka akan di redirect ke halaman 404 (Page not found).
        raise Http404("Outlet tidak ditemukan.")

def outlet_select_view(request, outlet_id):
    request.session['outlet_id'] = outlet_id

    if outlet_id == 'all':
        request.session['outlet_name'] = 'Semua Cabang'
    else:
        outlet = Outlet.objects.get(pk=outlet_id)
        request.session['outlet_name'] = outlet.name

    return HttpResponse(True)

def outlet_get_view(request):
    user_id         = request.user.id
    outlets = Outlet.objects.filter(user_id=user_id)
    data = serializers.serialize('json', outlets)
    
    return HttpResponse(data, content_type="text/json-comment-filtered")

# Material
@login_required
def material_view(request):
    user_id         = request.user.id
    materials = Material.objects.filter(user_id=user_id)
    context = {
        'materials': materials
    }

    return render(request, 'material/index.html', context)

@login_required
def material_create_view(request):
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    user_id         = request.user.id
    if request.method == 'POST':
        # membuat objek dari class TaskForm
        form = MaterialForm(request.POST, request.FILES)
        # Mengecek validasi form
        if form.is_valid():
            # Buat objek outlet baru dari form tanpa menyimpan ke database dulu
            new_outlet = form.save(commit=False)
            # Tambahkan user_id dari pengguna yang sedang terautentikasi
            new_outlet.user_id = user_id
            # Simpan objek outlet baru ke database
            new_outlet.save()
            # mengeset pesan sukses dan redirect ke halaman daftar task
            messages.success(request, 'Sukses Menambah Material baru.')
            return redirect('material.index')
    # Jika method-nya bukan POST
    else:
        # membuat objek dari class TaskForm
        form = MaterialForm()
    # merender template form dengan memparsing data form
    return render(request, 'material/form.html', {'form': form})

@login_required
def material_update_view(request, material_id):
    try:
        material = Material.objects.get(pk=material_id)
    except Material.DoesNotExist:
        raise Http404("Material tidak ditemukan.")
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sukses Mengubah Item.')
            return redirect('material.index')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'material/form.html', {'form': form})

def material_delete_view(request, material_id):
    try:
        material = Material.objects.get(pk=material_id)
        material.delete()
        messages.success(request, 'Sukses Menghapus Material.')
        return redirect('material.index')
    except Material.DoesNotExist:
        raise Http404("Material tidak ditemukan.")
    
# Product
@login_required
def product_view(request):
    user_id         = request.user.id
    items        = Item.objects.filter(type="JADI", user_id=user_id)
    context = {
        'items': items
    }

    return render(request, 'product/index.html', context)

def product_create_view(request):
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    user_id         = request.user.id

    if request.method == 'POST':
        # membuat objek dari class TaskForm
        form = ItemForm(request.POST, request.FILES)
        # Mengecek validasi form
        if form.is_valid():
             # Buat objek outlet baru dari form tanpa menyimpan ke database dulu
            new_outlet = form.save(commit=False)
            # Tambahkan user_id dari pengguna yang sedang terautentikasi
            new_outlet.user_id = user_id
            # Simpan objek outlet baru ke database
            new_outlet.save()
            # mengeset pesan sukses dan redirect ke halaman daftar task
            messages.success(request, 'Sukses Menambah Item baru.')
            return redirect('product.index')
    # Jika method-nya bukan POST
    else:
        # membuat objek dari class TaskForm
        form = ItemForm()
    # merender template form dengan memparsing data form
    return render(request, 'product/form.html', {'form': form})

@login_required
def product_update_view(request, product_id):
    try:
        item = Item.objects.get(pk=product_id)
    except Item.DoesNotExist:
        raise Http404("Item tidak ditemukan.")
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sukses Mengubah Item.')
            return redirect('product.index')
    else:
        form = ItemForm(instance=item)
    return render(request, 'product/form.html', {'form': form})

def product_delete_view(request, product_id):
    try:
        item = Item.objects.get(pk=product_id)
        item.delete()
        messages.success(request, 'Sukses Menghapus Item.')
        return redirect('product.index')
    except Item.DoesNotExist:
        raise Http404("Item tidak ditemukan.")
    
# Product recipe
@login_required
def product_recipe_view(request, product_id):
    items = Recipe.objects.filter(item_id=product_id)
    product = Item.objects.get(pk=product_id)
    context = {
        'items': items,
        'product': product
    }

    return render(request, 'product_recipe/index.html', context)

@login_required
def product_recipe_create_view(request, product_id):
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    if request.method == 'POST':
        # membuat objek dari class TaskForm
        form = RecipeForm(request.POST, request.FILES, user=request.user.id)
        # Mengecek validasi form
        if form.is_valid():
            # Membuat Task baru dengan data yang disubmit
            new_task = form.save(commit=False)
            new_task.item_id = product_id
            # Simpan data ke dalam table tasks
            new_task.save()
            # mengeset pesan sukses dan redirect ke halaman daftar task
            messages.success(request, 'Sukses Menambah Resep baru.')
            return redirect('product.recipe.index', product_id)
    # Jika method-nya bukan POST
    else:
        # membuat objek dari class TaskForm
        form = RecipeForm(user=request.user.id)
    # merender template form dengan memparsing data form
    return render(request, 'product_recipe/form.html', {'form': form, 'product_id': product_id})

def product_recipe_delete_view(request, product_id, material_id):
    try:
        recipe = Recipe.objects.filter(item_id=product_id).filter(material_id=material_id)
        recipe.delete()
        messages.success(request, 'Sukses Menghapus Resep.')
        return redirect('product.recipe.index', product_id)
    except Recipe.DoesNotExist:
        raise Http404("Resep tidak ditemukan.")

# Purchase
@login_required
def purchase_view(request):
    user_id         = request.user.id
    outlets         = Outlet.objects.filter(user_id=user_id)
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            purchases = Purchase.objects.filter(user_id=user_id).order_by('-created_at')
        else:
            purchases = Purchase.objects.filter(user_id=user_id).order_by('-created_at')
    else:
        purchases = Purchase.objects.filter(user_id=user_id)

    selected_outlet = request.GET.get('selected_outlet')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter by outlet and date range if provided
    if selected_outlet:
        try:
            purchases = purchases.filter(outlet_id=selected_outlet)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')  # Convert to datetime
            purchases = purchases.filter(created_at__gte=start_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')  # Convert to datetime
            end_date = end_date + timedelta(days=1) - timedelta(microseconds=1)
            purchases = purchases.filter(created_at__lte=end_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    context = {
        'purchases': purchases,
        'outlets': outlets,
        'selected_outlet': selected_outlet,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'purchase/index.html', context)

@login_required
def purchase_create_view(request):
    user_id         = request.user.id
    if request.method == 'POST':
        form = PurchaseForm(request.POST, user=request.user.id)
        if form.is_valid():
            # Buat objek outlet baru dari form tanpa menyimpan ke database dulu
            temp = form.save(commit=False)
            # Tambahkan user_id dari pengguna yang sedang terautentikasi
            temp.user_id = user_id
            # Simpan objek outlet baru ke database
            temp.save()

            # Simpan transaction dari purchase
            Transaction.objects.create(
                item_id = request.POST.get('item',''),
                outlet_id = request.POST.get('outlet',''),
                purchase_id = temp.id,
                user_id = user_id,
                type = 'purchase'
            )

            # Simpan stock dari sales
            try:
                obj = Stock.objects.get(outlet=request.POST.get('outlet',''), item=request.POST.get('item',''))
                obj.amount = int(obj.amount) + int(request.POST.get('amount',''))
                obj.save()
            except Stock.DoesNotExist:
                Stock.objects.create(
                    item_id = request.POST.get('item',''),
                    outlet_id = request.POST.get('outlet',''),
                    amount = request.POST.get('amount','0'),
                    user_id = user_id,
                )

            messages.success(request, 'Sukses menambah pembelian baru.')
            return redirect('purchase.index')
    else:
        form = PurchaseForm(user=request.user.id)
    return render(request, 'purchase/form.html', {'form': form})

@login_required
def purchase_update_view(request, purchase_id):
    try:
        purchase = Purchase.objects.get(pk=purchase_id)
    except Purchase.DoesNotExist:
        raise Http404("Pembelian tidak ditemukan.")
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase, user=request.user.id)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sukses Mengubah pembelian.')
            return redirect('purchase.index')
    else:
        form = PurchaseForm(instance=purchase, user=request.user.id)
    return render(request, 'purchase/form.html', {'form': form})

def purchase_delete_view(request, purchase_id):
    try:
        purchase = Purchase.objects.get(pk=purchase_id)
        purchase.delete()
        messages.success(request, 'Sukses menghapus pembelian.')
        return redirect('purchase.index')
    except Purchase.DoesNotExist:
        raise Http404("Pembelian tidak ditemukan.")

# Production
@login_required
def production_view(request):
    user_id         = request.user.id
    outlets         = Outlet.objects.filter(user_id=user_id)
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            productions = Production.objects.filter(user_id=user_id).order_by('-created_at')
        else:
            productions = Production.objects.objects.filter(user_id=user_id).order_by('-created_at')
    else:
        productions = Production.objects.filter(user_id=user_id)

    selected_outlet = request.GET.get('selected_outlet')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter by outlet and date range if provided
    if selected_outlet:
        try:
            productions = productions.filter(outlet_id=selected_outlet)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')  # Convert to datetime
            productions = productions.filter(created_at__gte=start_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')  # Convert to datetime
            end_date = end_date + timedelta(days=1) - timedelta(microseconds=1)
            productions = productions.filter(created_at__lte=end_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    context = {
        'productions': productions,
        'outlets': outlets,
        'selected_outlet': selected_outlet,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'production/index.html', context)

@login_required
def production_create_view(request):
    user_id         = request.user.id
    if request.method == 'POST':
        form = ProductionForm(request.POST)
        if form.is_valid():
            # Buat objek outlet baru dari form tanpa menyimpan ke database dulu
            temp = form.save(commit=False)
            # Tambahkan user_id dari pengguna yang sedang terautentikasi
            temp.user_id = user_id
            # Simpan objek outlet baru ke database
            temp.save()

            # Simpan stock dari production
            try:
                obj = Stock.objects.get(outlet=request.POST.get('outlet',''), item=request.POST.get('item',''))
                obj.amount = int(obj.amount) + int(request.POST.get('amount',''))
                obj.save()
            except Stock.DoesNotExist:
                Stock.objects.create(
                    item_id = request.POST.get('item',''),
                    outlet_id = request.POST.get('outlet',''),
                    amount = request.POST.get('amount','0'),
                    user_id = user_id
                )

            messages.success(request, 'Sukses menambah produksi baru.')
            return redirect('production.index')
    else:
        form = ProductionForm()
    return render(request, 'production/form.html', {'form': form})

def production_update_view(request, production_id):
    try:
        production = Production.objects.get(pk=production_id)
    except Production.DoesNotExist:
        raise Http404("Produksi tidak ditemukan.")
    if request.method == 'POST':
        form = ProductionForm(request.POST, instance=production, user=request.user.id)
        if form.is_valid():
            # prod = Production.objects.get(id=form.id)
            return HttpResponse(request.POST.get('pk',''))
            temp = form.save()

            # Simpan stock dari production
            try:
                obj = Stock.objects.get(outlet=request.POST.get('outlet',''), item=request.POST.get('item',''))
                return HttpResponse(prod.amount)
                obj.amount = int(obj.amount) - int(prod.amount) + int(request.POST.get('amount',''))
                obj.save()
            except Stock.DoesNotExist:
                Stock.objects.create(
                    item_id = request.POST.get('item',''),
                    outlet_id = request.POST.get('outlet',''),
                    amount = request.POST.get('amount','0'),
                    user_id = user_id,
                )
            
            messages.success(request, 'Sukses Mengubah Produksi.')
            return redirect('production.index')
    else:
        form = ProductionForm(instance=production, user=request.user.id)
    return render(request, 'production/form.html', {'form': form})

def production_delete_view(request, production_id):
    try:
        production = Production.objects.get(pk=production_id)
        production.delete()
        messages.success(request, 'Sukses menghapus pembelian.')
        return redirect('production.index')
    except Production.DoesNotExist:
        raise Http404("Pembelian tidak ditemukan.")

# Sales
@login_required
def sales_view(request):
    user_id         = request.user.id
    outlets         = Outlet.objects.filter(user_id=user_id)
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            sales = Sales.objects.filter(user_id=user_id).order_by('-created_at')
        else:
            sales = Sales.objects.filter(user_id=user_id).order_by('-created_at')
    else:
        sales = Sales.objects.filter(user_id=user_id)

    selected_outlet = request.GET.get('selected_outlet')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter by outlet and date range if provided
    if selected_outlet:
        try:
            sales = sales.filter(outlet_id=selected_outlet)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')  # Convert to datetime
            sales = sales.filter(created_at__gte=start_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')  # Convert to datetime
            end_date = end_date + timedelta(days=1) - timedelta(microseconds=1)
            sales = sales.filter(created_at__lte=end_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    context = {
        'sales': sales,
        'outlets': outlets,
        'selected_outlet': selected_outlet,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'sales/index.html', context)

@login_required
def sales_create_view(request):
    user_id         = request.user.id
    if request.method == 'POST':
        form = SalesForm(request.POST, user=request.user.id)
        if form.is_valid():
            # Buat objek outlet baru dari form tanpa menyimpan ke database dulu
            temp = form.save(commit=False)
            # Tambahkan user_id dari pengguna yang sedang terautentikasi
            temp.user_id = user_id
            # Simpan objek outlet baru ke database
            temp.save()

            # Simpan transaction dari sales
            Transaction.objects.create(
                item_id = request.POST.get('item',''),
                outlet_id = request.POST.get('outlet',''),
                sales_id = temp.id,
                type = 'sales',
                user_id = user_id
            )

            # Simpan stock dari sales
            try:
                obj = Stock.objects.get(outlet=request.POST.get('outlet',''), item=request.POST.get('item',''))
                obj.amount = int(obj.amount) - int(request.POST.get('amount',''))
                obj.save()
            except Stock.DoesNotExist:
                Stock.objects.create(
                    item_id = request.POST.get('item',''),
                    outlet_id = request.POST.get('outlet',''),
                    amount = -int(request.POST.get('amount', '0')),
                    user_id = user_id,
                )

            messages.success(request, 'Sukses menambah penjualan baru.')
            return redirect('sales.index')
    else:
        form = SalesForm(user=request.user.id)
    return render(request, 'sales/form.html', {'form': form})

@login_required
def sales_update_view(request, sales_id):
    try:
        sales = Sales.objects.get(pk=sales_id)
    except Sales.DoesNotExist:
        raise Http404("Penjualan tidak ditemukan.")
    if request.method == 'POST':
        form = SalesForm(request.POST, instance=sales, user=request.user.id)
        if form.is_valid():
            form.save()

            # Simpan stock dari production
            try:
                obj = Stock.objects.get(outlet=request.POST.get('outlet',''), item=request.POST.get('item',''))
                obj.amount = int(obj.amount) - int(request.POST.get('amount',''))
                obj.save()
            except Stock.DoesNotExist:
                Stock.objects.create(
                    item_id = request.POST.get('item',''),
                    outlet_id = request.POST.get('outlet',''),
                    amount = request.POST.get('amount',''),
                    user_id = user_id,
                )

            messages.success(request, 'Sukses Mengubah penjualan.')
            return redirect('sales.index')
    else:
        form = SalesForm(instance=sales, user=request.user.id)
    return render(request, 'sales/form.html', {'form': form})

def sales_delete_view(request, sales_id):
    try:
        sales = Sales.objects.get(pk=sales_id)
        sales.delete()
        messages.success(request, 'Sukses menghapus penjualan.')
        return redirect('sales.index')
    except Sales.DoesNotExist:
        raise Http404("Penjualan tidak ditemukan.")

# Transaction
@login_required
def transaction_view(request):
    user_id         = request.user.id
    outlets         = Outlet.objects.filter(user_id=user_id)
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            transactions = Transaction.objects.filter(user_id=user_id).order_by('-created_at')
        else:
            transactions = Transaction.objects.filter(user_id=user_id).order_by('-created_at')
    else:
        transactions = Transaction.objects.filter(user_id=user_id)

    selected_outlet = request.GET.get('selected_outlet')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter by outlet and date range if provided
    if selected_outlet:
        try:
            transactions = transactions.filter(outlet_id=selected_outlet)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')  # Convert to datetime
            transactions = transactions.filter(created_at__gte=start_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')  # Convert to datetime
            end_date = end_date + timedelta(days=1) - timedelta(microseconds=1)
            transactions = transactions.filter(created_at__lte=end_date)
        except ValueError:
            pass  # Handle invalid date format if necessary

    context = {
        'transactions': transactions,
        'outlets': outlets,
        'selected_outlet': selected_outlet,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'transaction/index.html', context)

# Stocks
@login_required
def stock_view(request):
    user_id         = request.user.id
    outlets         = Outlet.objects.filter(user_id=user_id)
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            stocks = Stock.objects.filter(user_id=user_id)
        else:
            stocks = Stock.objects.filter(user_id=user_id)
    else:
        stocks = Stock.objects.filter(user_id=user_id)

    selected_outlet = request.GET.get('selected_outlet')

    # Filter by outlet and date range if provided
    if selected_outlet:
        try:
            stocks = stocks.filter(outlet_id=selected_outlet)
        except ValueError:
            pass  # Handle invalid date format if necessary

    context = {
        'stocks': stocks,
        'outlets': outlets,
    }

    return render(request, 'stock/index.html', context)

# Export
@login_required
def export_view(request):
    user_id         = request.user.id
    if request.method == 'POST':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ExportData.csv"'        
        writer = csv.writer(response)
        writer.writerow(['Sales Data'])
        writer.writerow(['No', 'Nama Barang','Biaya Pesan','Permintaan Bahan Baku','Biaya Simpan','Biaya Kekurangan','Harga Produk','Lead Time Pemenuhan', 'Standar Deviasi'])
        items = Item.objects.filter(type="JADI", user_id=user_id).all()
        for idx, item in enumerate(items):
            sales = Sales.objects.filter(user_id=user_id).filter(item_id=item.id)

            # return HttpResponse(len(sales))
            sales_count = 0
            sales_list = []

            for sale in sales:
                sales_count += sale.amount
                sales_list.append(sale.amount)

            n = len(sales_list)
            if n < 2:
                if not sales:
                    standar_deviasi = 1
                else:
                    standar_deviasi = sales[0].amount
            else:
                standar_deviasi = np.std(sales_list)

            biaya_kekurangan = (item.price * 7.5 / 100) + item.price

            # Write row excel
            row = [idx+1, item.name, item.biaya_pesan, sales_count, 200000, biaya_kekurangan, item.price, item.lead_time, standar_deviasi]
            writer.writerow(row)
        return response
    
    context = {
        # 'transactions': transactions
    }

    return render(request, 'export/index.html', context)

def questionnaire_view(request):
    respondents = Responden.objects.all().order_by('-submitted_at')

    # return HttpResponse(respondents)

    context = {
        'respondents': respondents,
    }

    return render(request, 'questionnaire/index.html', context)

def questionnaire_isi_view(request):
    if request.method == 'POST':
        form = RespondenForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            # Use transaction so everything saves together or not at all
            with transaction.atomic():

                # 1. Save personal info to Responden
                responden = Responden.objects.create(
                    nama                = data['nama'],
                    usia                = data['usia'],
                    pendidikan_terakhir = data['pendidikan_terakhir'],
                    umkm                = data['umkm'],
                    address             = data['address'],
                    phone_number        = data['phone_number'],
                )

                # 2. Loop through all Likert answers and save to Jawaban
                jawaban_list = []
                for field_name, value in data.items():
                    # Only process fields that match a variabel prefix (e.g. PEOU_1, PU_2)
                    parts = field_name.split('_')
                    prefix = parts[0]  # e.g. "PEOU", "PU", "CONF"

                    if prefix in VARIABEL_MAP:
                        jawaban_list.append(Jawaban(
                            responden = responden,
                            variabel  = VARIABEL_MAP[prefix],
                            kode_item = field_name,   # e.g. "PEOU_1"
                            skor      = int(value),
                        ))

                # bulk_create saves all Jawaban rows in one query
                Jawaban.objects.bulk_create(jawaban_list)

            messages.success(request, 'Terima kasih! Jawaban Anda telah tersimpan.')
            return redirect('questionnaire.sukses')

        # Form invalid — re-render with errors
        return render(request, 'questionnaire/form.html', {'form': form})

    # GET request — show empty form
    form = RespondenForm()
    return render(request, 'questionnaire/form.html', {'form': form})

def questionnaire_detail_view(request, respondent_id):
    responden = get_object_or_404(Responden, pk=respondent_id)

    # Build initial data dict from saved Jawaban rows
    initial_data = {
        'nama'                : responden.nama,
        'usia'                : responden.usia,
        'pendidikan_terakhir' : responden.pendidikan_terakhir,
        'umkm'                : responden.umkm,
        'address'             : responden.address,
        'phone_number'        : responden.phone_number,
    }

    # Add each Likert answer — kode_item is already the field name e.g. "PEOU_1"
    for jawaban in responden.jawaban.all():
        initial_data[jawaban.kode_item] = str(jawaban.skor)  # str() because ChoiceField expects string

    # Pass initial data into the form — this pre-selects all the radio buttons
    form = RespondenForm(initial=initial_data)

    return render(request, 'questionnaire/detail.html', {
        'form'      : form,
        'responden' : responden,
    })

def questionnaire_sukses_view(request):
    return render(request, 'questionnaire/success.html')

def questionnaire_export_view(request):
    if request.method == 'POST':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="DataKuesioner.csv"'

        writer = csv.writer(response)

        # Header row
        writer.writerow([
            'No', 'Nama', 'Usia', 'Pendidikan Terakhir', 'Asal UMKM',
            'Alamat', 'Nomor HP', 'Tanggal Submit',
            *JAWABAN_CODES  # unpack all Likert column headers
        ])

        respondents = Responden.objects.all().order_by('-submitted_at')

        for idx, responden in enumerate(respondents):
            # Build a dict of kode_item -> skor for quick lookup
            jawaban_map = {
                j.kode_item: j.skor
                for j in responden.jawaban.all()
            }

            # Get each score in order, default to '' if missing
            scores = [jawaban_map.get(code, '') for code in JAWABAN_CODES]

            writer.writerow([
                idx + 1,
                responden.nama,
                responden.usia,
                responden.pendidikan_terakhir,
                responden.umkm,
                responden.address,
                responden.phone_number,
                responden.submitted_at.strftime('%d-%m-%Y %H:%M'),
                *scores
            ])

        return response

    return render(request, 'questionnaire/index.html')

# Periodic Review
def calculate_inventory_cost(product, to):
    A = product["biaya_pesan"]
    D = product["permintaan_baku"] / 5
    vr = product["biaya_simpan"] / 5
    B3 = product["biaya_kekurangan"]
    L = product["lead_time"]
    Std = product["standar_deviasi"]
    k = round(vr / (vr + B3), 2)
    sigma_RL = (to + L) * Std

    # Mencari Q
    Q = math.sqrt((2 * A * D) / vr)
    
    if Q <= 0 :
       biaya_pesan = (A * D)
    else:
    # Mencari total biaya pesan
       biaya_pesan = (A * D) / Q

   
    # Mencari total biaya simpan
    biaya_simpan = ((Q / 2) + (k * sigma_RL) * vr)

    # Mencari total biaya kekurangan
    if Q <= 0 :
       biaya_kekurangan = (B3 * sigma_RL * 0.216 * D)
    else:
    # Mencari total biaya pesan
       biaya_kekurangan = (B3 * sigma_RL * 0.216 * D) / Q
    

    # Hitung ongkos total dan masukkan ke dalam list
    ongkos_total = biaya_pesan + biaya_simpan + biaya_kekurangan
    
    return ongkos_total

def periodic_view(request):
    if request.method == 'POST':
        array = []
        data = []

        algorithm = request.POST.get('algorithm')

        # read_file = request.FILES['file']
        # csv_data = pd.read_csv(read_file, header=1, encoding="UTF-8")

        # for dt in csv_data.values:
        #     array_data = {}
        #     array_data['nama_barang'] = dt[1]
        #     array_data['biaya_pesan'] = dt[2]
        #     array_data['permintaan_baku'] = dt[3]
        #     array_data['biaya_simpan'] = dt[4]
        #     array_data['biaya_kekurangan'] = dt[5]
        #     array_data['harga_material'] = dt[6]
        #     array_data['lead_time'] = dt[7] / 100
        #     array_data['standar_deviasi'] = dt[8]

        #     array.append(array_data)

        if algorithm == 'pso':
            items = Item.objects.filter(type="JADI")

            data = []

            initial_cost_total = 0
            optimized_cost_total = 0

            # Ambil rentang periode sales keseluruhan
            sales_range = Sales.objects.aggregate(
                min_date=Min('created_at'),
                max_date=Max('created_at'),
            )

            min_date = sales_range['min_date']
            max_date = sales_range['max_date']

            if not min_date or not max_date:
                return render(request, 'periodic/calculation.html', {
                    'data': [],
                    'message': 'Data sales tidak ditemukan.'
                })

            start_date = min_date.date()
            end_date = max_date.date()

            period_days = (end_date - start_date).days + 1
            period_days = max(1, period_days)

            # Hyperparameter PSO
            min_R = 1
            max_R = 30
            num_particles = 40
            maxiter = 100

            # Asumsi biaya
            h_per_month = 2000
            holding_cost_per_unit_per_day = h_per_month / 30

            for item in items:
                # =====================================================
                # 1. Aggregate demand harian
                # =====================================================
                sales_qs = (
                    Sales.objects
                    .filter(item_id=item.id)
                    .order_by('created_at')
                )

                if not sales_qs.exists():
                    continue

                sales_by_day = defaultdict(float)

                for sale in sales_qs:
                    if not sale.created_at:
                        continue

                    # Kalau created_at adalah datetime
                    if hasattr(sale.created_at, 'date'):
                        day = sale.created_at.date()
                    else:
                        # fallback kalau ternyata created_at berupa string
                        day = datetime.fromisoformat(str(sale.created_at)).date()

                    sales_by_day[day] += float(sale.amount or 0)

                if not sales_by_day:
                    continue

                # Pakai range global yang sudah kamu hitung sebelumnya
                demand_list = []
                current_date = start_date

                while current_date <= end_date:
                    demand_list.append(sales_by_day.get(current_date, 0))
                    current_date += timedelta(days=1)

                if sum(demand_list) <= 0:
                    continue

                # =====================================================
                # 2. Parameter dasar
                # =====================================================
                D = sum(demand_list)
                daily_mean = np.mean(demand_list)
                sigma = np.std(demand_list, ddof=1) if len(demand_list) > 1 else 0

                A = item.biaya_pesan or 0
                P = item.price or 0

                # Biaya kekurangan.
                # Untuk inventory murni, pakai penalty kekurangan saja.
                # Kalau kamu memang mau menghitung lost sales sebesar harga barang,
                # bisa ubah menjadi: Cu = P + (P * 7.5 / 100)
                Cu = P * 7.5 / 100

                lead_time_days = item.lead_time or 0

                # Untuk rumus Hadley, h harus biaya simpan per unit selama periode data.
                h = holding_cost_per_unit_per_day * period_days

                # Lead time dalam fraksi periode untuk Hadley.
                L = lead_time_days / period_days if period_days > 0 else 0

                # =====================================================
                # 3. Initial R, s, S dari Hadley / EOQ
                # =====================================================
                initial_to = find_initial_to(
                    A=A,
                    D=D,
                    h=h,
                )

                initial_days = to_to_days(initial_to, period_days)
                initial_days = max(min_R, min(max_R, initial_days))

                # Hitung ulang T0 berdasarkan R hari yang sudah dibulatkan
                initial_to = days_to_to(initial_days, period_days)

                ss_initial = calculate_s_s_policy(
                    to=initial_to,
                    D=D,
                    A=A,
                    h=h,
                    Cu=Cu,
                    L=L,
                    sigma=sigma,
                )

                initial_s = max(0, int(round(ss_initial['s'])))
                initial_S = max(initial_s + 1, int(round(ss_initial['S'])))

                # Simulasikan initial policy supaya basis biaya sama dengan PSO
                initial_simulation = simulate_inventory_rss(
                    demand_list=demand_list,
                    R=initial_days,
                    s=initial_s,
                    S=initial_S,
                    lead_time_days=lead_time_days,
                    ordering_cost=A,
                    holding_cost_per_unit_per_day=holding_cost_per_unit_per_day,
                    shortage_cost_per_unit=Cu,
                    initial_stock=initial_S,
                )

                initial_cost = initial_simulation['total_inventory_cost']

                # =====================================================
                # 4. PSO mencari kombinasi R, s, S optimal
                # =====================================================
                # Bound stok jangan terlalu kecil, supaya PSO punya ruang mencari.
                # Rumus ini bisa kamu sesuaikan kalau hasil S terlalu besar/kecil.
                max_stock_bound = max(
                    10,
                    int(D),
                    int(daily_mean * (max_R + lead_time_days) * 3),
                    initial_S * 2,
                )

                pso_result = find_optimal_rss_pso(
                    demand_list=demand_list,
                    lead_time_days=lead_time_days,
                    ordering_cost=A,
                    holding_cost_per_unit_per_day=holding_cost_per_unit_per_day,
                    shortage_cost_per_unit=Cu,

                    min_R=min_R,
                    max_R=max_R,

                    min_s=0,
                    max_s=max_stock_bound,

                    min_S=1,
                    max_S=max_stock_bound,

                    num_particles=num_particles,
                    maxiter=maxiter,
                )

                optimal_R = pso_result['R']
                optimal_s = pso_result['s']
                optimal_S = pso_result['S']

                optimal_simulation = pso_result['result']
                optimized_cost = optimal_simulation['total_inventory_cost']

                # =====================================================
                # 5. Summary biaya
                # =====================================================
                initial_cost_total += initial_cost
                optimized_cost_total += optimized_cost

                penghematan = initial_cost - optimized_cost
                penghematan_persen = (
                    penghematan / initial_cost * 100
                    if initial_cost > 0 else 0
                )

                data.append({
                    'nama_barang': item.name,

                    'D': round(D),
                    'daily_mean': round(daily_mean, 2),
                    'sigma': round(sigma, 2),
                    'period_days': period_days,

                    # ==========================
                    # Sebelum PSO / Initial
                    # ==========================
                    'initial_review_interval_days': initial_days,
                    'initial_s': initial_s,
                    'initial_S': initial_S,
                    'initial_N': round(initial_simulation['total_stockout_qty'], 2),
                    'initial_order_count': initial_simulation['order_count'],
                    'initial_average_stock': round(initial_simulation['average_stock'], 2),

                    'initial_ordering_cost': round(initial_simulation['ordering_cost']),
                    'initial_holding_cost': round(initial_simulation['holding_cost']),
                    'initial_shortage_cost': round(initial_simulation['shortage_cost']),
                    'initial_biaya_inventory': round(initial_cost),

                    # ==========================
                    # Sesudah PSO / Optimal
                    # ==========================
                    'optimal_review_interval_days': optimal_R,
                    'optimal_s': optimal_s,
                    'optimal_S': optimal_S,
                    'optimal_N': round(optimal_simulation['total_stockout_qty'], 2),
                    'optimal_order_count': optimal_simulation['order_count'],
                    'optimal_average_stock': round(optimal_simulation['average_stock'], 2),

                    'optimal_ordering_cost': round(optimal_simulation['ordering_cost']),
                    'optimal_holding_cost': round(optimal_simulation['holding_cost']),
                    'optimal_shortage_cost': round(optimal_simulation['shortage_cost']),
                    'optimal_biaya_inventory': round(optimized_cost),

                    # ==========================
                    # Selisih
                    # ==========================
                    'penghematan': round(penghematan),
                    'penghematan_persen': round(penghematan_persen, 2),
                })

            context = {
                'data': data,
                'period_days': period_days,

                'initial_cost_total': round(initial_cost_total),
                'optimized_cost_total': round(optimized_cost_total),

                'total_penghematan': round(initial_cost_total - optimized_cost_total),
                'total_penghematan_pct': round(
                    (initial_cost_total - optimized_cost_total) / initial_cost_total * 100,
                    2
                ) if initial_cost_total > 0 else 0,
            }

            return render(request, 'periodic/calculation.html', context)
        else:
            # ---------------------------------------------------------------- #
            # Parse POST parameters
            # ---------------------------------------------------------------- #
            pop_size        = _parse_post_int  (request.POST, 'population_size', 30)
            num_generations = _parse_post_int  (request.POST, 'num_generations', 50)
            crossover_rate  = _parse_post_float(request.POST, 'crossover_rate',  0.8)
            mutation_rate   = _parse_post_float(request.POST, 'mutation_rate',   0.1)
    
            use_bo          = request.POST.get('use_bo', 'false').lower() == 'true'
            bo_n_calls      = _parse_post_int  (request.POST, 'bo_n_calls',    BO_N_CALLS)
            bo_n_initial    = _parse_post_int  (request.POST, 'bo_n_initial',  BO_N_INITIAL)
            stockout_weight = _parse_post_float(request.POST, 'stockout_weight', BO_STOCKOUT_WEIGHT)

            items   = Item.objects.filter(type="JADI")
    
            total_start    = time.time()
            total_duration = 0.0

            total_data_dict               = {}
            first_outlet_inventory_levels = {}
            outlet_inventory_levels       = {}
            data_all                      = []

            # -------------------------------------------------------------- #
            # BO PHASE — jalankan SEKALI untuk semua item, pakai outlet 3
            # sebagai data representatif. Hasilnya di-cache ke global_bo_params.
            # -------------------------------------------------------------- #
            global_bo_params = None
            bo_duration      = 0.0

            if use_bo:
                products_data = []  # list of (product_dict, daily_sales, daily_purchases)

                for item in items:
                    try:
                        bo_sales_qs = (Sales.objects.filter(item_id=item.id)
                                    .values('created_at')
                                    .annotate(total_sales=Sum('amount')))
                        bo_purch_qs = (Purchase.objects.filter(item_id=item.id)
                                    .values('created_at')
                                    .annotate(total_purchases=Sum('amount')))

                        bo_sales_dict = {r['created_at'].date(): r['total_sales']     for r in bo_sales_qs}
                        bo_purch_dict = {r['created_at'].date(): r['total_purchases'] for r in bo_purch_qs}

                        if not bo_sales_dict:
                            continue

                        bo_start_date  = min(bo_sales_dict.keys())
                        bo_end_date    = bo_start_date + timedelta(days=59)
                        bo_daily_sales = []
                        bo_daily_purch = []
                        cur = bo_start_date
                        while cur <= bo_end_date:
                            bo_daily_sales.append(bo_sales_dict.get(cur, 0))
                            bo_daily_purch.append(bo_purch_dict.get(cur, 0))
                            cur += timedelta(days=1)

                        bo_total_sales = sum(bo_daily_sales)
                        bo_std         = np.std(bo_daily_sales) if len(bo_daily_sales) > 1 else 1

                        bo_product = {
                            'nama_barang':      item.name,
                            'biaya_pesan':      item.biaya_pesan,
                            'biaya_order':      20000,
                            'permintaan_baku':  bo_total_sales if bo_total_sales > 0 else 1,
                            'biaya_simpan':     5000,
                            'biaya_kekurangan': round((item.price * 7.5 / 100) + item.price),
                            'harga_produk':     item.price,
                            'lead_time':        item.lead_time / 100,
                            'standar_deviasi':  bo_std,
                        }

                        products_data.append((bo_product, bo_daily_sales, bo_daily_purch))

                    except Exception:
                        continue

                if products_data:
                    bo_start = time.time()
                    global_bo_params, _, _ = bo_optimize_hyperparameters_global(
                        products_data,
                        n_calls          = bo_n_calls,
                        n_initial_points = bo_n_initial,
                        stockout_weight  = stockout_weight,
                    )
                    bo_duration = time.time() - bo_start

            # -------------------------------------------------------------- #
            # GA PHASE — loop outlets × items, gunakan cached BO params
            # -------------------------------------------------------------- #
            biaya_simpan = 5000
            biaya_order  = 20000

            first_combined_inventory_level = [0] * 60
            combined_inventory_level       = [0] * 60
            combined_purchases_list        = [0] * 60
            combined_sales_list            = [0] * 60
            first_single_inventory_level   = [0] * 60
            single_inventory_level         = [0] * 60
            single_purchases_list          = [0] * 60
            single_sales_list              = [0] * 60
            first_multiple_inventory_data  = []
            multiple_inventory_data        = []

            data = []

            for item_index, item in enumerate(items):
                sales       = Sales.objects.filter(item_id=item.id)

                sales_list_raw  = [sale.amount for sale in sales]
                total_sales     = sum(sales_list_raw)
                standar_deviasi = (np.std(sales_list_raw) if len(sales_list_raw) > 1
                                else (sales_list_raw[0] if sales_list_raw else 1))

                sales_data     = (Sales.objects.filter(item_id=item.id)
                                .values('created_at').annotate(total_sales=Sum('amount')))
                purchases_data = (Purchase.objects.filter(item_id=item.id)
                                .values('created_at').annotate(total_purchases=Sum('amount')))

                sales_dict     = {s['created_at'].date(): s['total_sales']     for s in sales_data}
                purchases_dict = {p['created_at'].date(): p['total_purchases'] for p in purchases_data}

                start_date = min(sales_dict.keys(), default=datetime.today().date())
                end_date   = start_date + timedelta(days=59)

                daily_sales     = []
                daily_purchases = []
                cur = start_date
                while cur <= end_date:
                    daily_sales.append(sales_dict.get(cur, 0))
                    daily_purchases.append(purchases_dict.get(cur, 0))
                    cur += timedelta(days=1)

                product = {
                    'nama_barang':      item.name,
                    'biaya_pesan':      item.biaya_pesan,
                    'biaya_order':      biaya_order,
                    'permintaan_baku':  total_sales,
                    'biaya_simpan':     biaya_simpan,
                    'biaya_kekurangan': round((item.price * 7.5 / 100) + item.price),
                    'harga_produk':     item.price,
                    'lead_time':        item.lead_time / 100,
                    'standar_deviasi':  standar_deviasi,
                }

                # ---- Resolve hyperparameters dari cache BO ----------- #
                if global_bo_params:
                    final_pop = global_bo_params['population_size']
                    final_gen = num_generations
                    final_cr  = global_bo_params['crossover_rate']
                    final_mr  = global_bo_params['mutation_rate']
                    bo_meta   = {
                        'used':        True,
                        'best_params': global_bo_params,
                        'best_score':  None,
                        'history':     [],
                        'bo_duration': bo_duration,
                    }
                else:
                    final_pop = pop_size
                    final_gen = num_generations
                    final_cr  = crossover_rate
                    final_mr  = mutation_rate
                    bo_meta   = {
                        'used':        False,
                        'best_params': None,
                        'best_score':  None,
                        'history':     [],
                        'bo_duration': 0.0,
                    }

                # ---- Jalankan GA dengan hyperparameter yang sudah di-resolve ---- #
                ga_result = genetic_algorithm(
                    product, final_pop, final_gen, final_cr, final_mr,
                    daily_sales, daily_purchases,
                )

                (_, _, _, _, _,
                inventory_level_list, purchases_list, sales_list,
                total_demand, total_lost, max_inventory,
                purchases_freq, purchases_total, restock_data,
                best_product, best_demand,
                best_total_cost, best_to,
                best_R, best_s, best_S, best_T,
                first_R, first_s, first_S, first_T,
                first_purchases_freq, first_total_lost, first_demand,
                first_purchases_total,
                first_inventory_level_list, first_restock_data,
                first_calc_duration, best_calc_duration) = ga_result

                # ---- FIRST (analytical baseline) cost --------------- #
                temp_first_start   = time.time()
                first_half_demand  = first_demand[:first_T]
                first_total_demand = round(sum(first_half_demand))
                first_mean_daily   = np.mean(first_half_demand) if first_half_demand else 0
                first_std_monthly  = np.std(first_half_demand, ddof=1) if len(first_half_demand) > 1 else 0
                first_std_daily    = first_std_monthly / np.sqrt(first_T) if first_T > 0 else 1e-9
                first_total_daily_dmd = round(first_total_demand / first_T) if first_T > 0 else 0

                first_restock_nz     = [x for x in first_restock_data if x != 0]
                first_restock_z      = [x for x in first_restock_data if x == 0]
                first_restock_result = first_restock_nz + first_restock_z

                first_stock_history = []
                first_stock = 0
                for i in range(first_T):
                    first_stock += round(first_restock_result[i])
                    first_stock -= round(first_restock_data[i])
                    first_stock_history.append(first_stock)

                for day in range(min(first_T, len(first_inventory_level_list))):
                    first_combined_inventory_level[day] += first_inventory_level_list[day]

                first_multiple_inventory_data.append({
                    'inventory':  first_inventory_level_list[:first_T],
                    'item_index': item_index,
                    'item_name':  item.name
                })

                if item_index == 1:
                    for day in range(min(first_T, len(first_inventory_level_list))):
                        first_single_inventory_level[day] += first_inventory_level_list[day]

                fp_freq        = max(first_purchases_freq, 1)
                first_c_order  = biaya_order * (first_T / (fp_freq * first_R))
                first_c_hold   = (biaya_simpan * ((first_S + first_s) / 2)
                                + (first_total_demand * first_R) / fp_freq)
                first_total_so = round(sum(first_total_lost))

                if first_std_daily > 0:
                    def integrand_first(x):
                        return (x - first_total_daily_dmd) * norm.pdf(x, first_mean_daily, first_std_daily)
                    E_Rv_first, _ = quad(integrand_first, first_total_daily_dmd, np.inf)
                else:
                    E_Rv_first = 0.0

                first_c_stockout   = product["biaya_kekurangan"] * E_Rv_first
                first_c_total      = first_c_order + first_c_hold + first_c_stockout
                first_calc_duration += time.time() - temp_first_start

                # ---- BEST (GA-optimised) cost ----------------------- #
                temp_best_start = time.time()
                half_demand     = best_demand[:best_T]
                tot_demand_best = round(sum(half_demand))
                mean_daily      = np.mean(half_demand) if half_demand else 0
                std_monthly     = np.std(half_demand, ddof=1) if len(half_demand) > 1 else 0
                std_daily       = std_monthly / np.sqrt(best_T) if best_T > 0 else 1e-9
                total_daily_dmd = round(tot_demand_best / best_T) if best_T > 0 else 0

                restock_nz     = [x for x in restock_data if x != 0]
                restock_z      = [x for x in restock_data if x == 0]
                restock_result = restock_nz + restock_z

                stock_history = []
                stock = 0
                for i in range(best_T):
                    stock += round(restock_result[i])
                    stock -= round(restock_data[i])
                    stock_history.append(stock)

                for day in range(min(best_T, len(inventory_level_list))):
                    combined_inventory_level[day] += inventory_level_list[day]
                    combined_purchases_list[day]  += purchases_list[day]
                    combined_sales_list[day]      += sales_list[day]

                    multiple_inventory_data.append({
                        'inventory':  inventory_level_list[:best_T],
                        'purchases':  purchases_list[:best_T],
                        'sales':      sales_list[:best_T],
                        'item_index': item_index,
                        'item_name':  item.name
                    })

                if item_index == 1:
                    for day in range(min(best_T, len(inventory_level_list))):
                        single_inventory_level[day]  += inventory_level_list[day]
                        single_purchases_list[day]   += purchases_list[day]
                        single_sales_list[day]       += sales_list[day]

                mod_pf   = max(purchases_freq, 1)
                c_order  = biaya_order * (best_T / (mod_pf * best_R))
                c_hold   = (biaya_simpan * round((best_S + best_s) / 2)
                            + round((tot_demand_best * best_R) / mod_pf))
                total_so = round(sum(total_lost))

                if std_daily > 0:
                    def integrand_best(x):
                        return (x - total_daily_dmd) * norm.pdf(x, mean_daily, std_daily)
                    E_Rv_best, _ = quad(integrand_best, total_daily_dmd, np.inf)
                else:
                    E_Rv_best = 0.0

                c_stockout = product["biaya_kekurangan"] * E_Rv_best
                c_total    = c_order + c_hold + c_stockout
                best_calc_duration += time.time() - temp_best_start

                item_data = {
                    'first_c_order':         round(first_c_order),
                    'first_c_hold':          round(first_c_hold),
                    'first_c_stockout':      round(first_c_stockout),
                    'first_c_total':         round(first_c_total),
                    'first_purchases_freq':  round(fp_freq),
                    'first_purchases_total': round(first_purchases_total),
                    'first_stockout_total':  first_total_so,
                    'first_stockout_mean':   [first_total_so],
                    'first_restock_data':    [a - b for a, b in zip(half_demand, first_restock_data[:len(half_demand)])],
                    'first_stock_history':   first_stock_history,
                    'first_timespan':        first_T,
                    'first_calc_duration':   first_calc_duration,
                    'first_R':        first_R,
                    'first_s':        first_s,
                    'first_S':        first_S,
                    'c_order':               round(c_order),
                    'c_hold':                round(c_hold),
                    'c_stockout':            round(c_stockout),
                    'c_total':               round(c_total),
                    'purchases_freq':        round(purchases_freq),
                    'purchases_total':       round(purchases_total),
                    'stockout_total':        total_so,
                    'stockout_mean':         [total_so],
                    'restock_data':          [a - b for a, b in zip(half_demand, restock_data[:len(half_demand)])],
                    'stock_history':         stock_history,
                    'timespan':              best_T,
                    'best_calc_duration':    best_calc_duration,
                    'best_R':         best_R,
                    'best_s':         best_s,
                    'best_S':         best_S,
                    'bo_used':               bo_meta['used'],
                    'bo_best_params':        bo_meta['best_params'],
                    'bo_duration':           round(bo_meta['bo_duration'], 2),
                }

                # ---- Aggregate ke total_data_dict ------------------- #
                name = product["nama_barang"]
                if name in total_data_dict:
                    td = total_data_dict[name]
                    for fkey in ('first_c_order', 'first_c_hold', 'first_c_stockout',
                                'first_c_total', 'first_purchases_freq',
                                'first_purchases_total', 'first_stockout_total',
                                'first_calc_duration', 'first_R',
                                'outlet_first_s', 'outlet_first_S',
                                'c_order', 'c_hold', 'c_stockout', 'c_total',
                                'purchases_total', 'stockout_total',
                                'best_calc_duration', 'outlet_best_R',
                                'outlet_best_s', 'outlet_best_S'):
                        td[fkey] += item_data[fkey]
                    td['purchases_freq']      += item_data['purchases_freq']
                    td['first_stockout_mean'] += item_data['first_stockout_mean']
                    td['stockout_mean']       += item_data['stockout_mean']
                    for lkey in ('first_restock_data', 'first_stock_history',
                                'restock_data', 'stock_history'):
                        td[lkey] = [a + b for a, b in zip(td[lkey], item_data[lkey])]
                    td['first_timespan'] = min(td['first_timespan'], item_data['first_timespan'])
                    td['timespan']       = min(td['timespan'],       item_data['timespan'])
                else:
                    total_data_dict[name] = {
                        'nama_barang': name,
                        **{k: item_data[k] for k in item_data if k != 'outlet_id'},
                    }
                    total_data_dict[name]['purchases_freq'] = (
                        item_data['purchases_freq']
                    )

                data.append({
                    'nama_barang':           product["nama_barang"],
                    'first_c_order':         round(first_c_order),
                    'first_c_hold':          round(first_c_hold),
                    'first_c_stockout':      round(first_c_stockout),
                    'first_c_total':         round(first_c_total),
                    'first_purchases_freq':  round(fp_freq),
                    'first_purchases_total': round(first_purchases_total),
                    'first_stockout_total':  first_total_so,
                    'first_timespan':        first_T,
                    'first_calc_duration':   first_calc_duration,
                    'first_R':               first_R,
                    'first_s':        first_s,
                    'first_S':        first_S,
                    'c_order':               round(c_order),
                    'c_hold':                round(c_hold),
                    'c_stockout':            round(c_stockout),
                    'c_total':               round(c_total),
                    'purchases_freq':        round(purchases_freq),
                    'purchases_total':       round(purchases_total),
                    'stockout_total':        total_so,
                    'timespan':              best_T,
                    'best_calc_duration':    best_calc_duration,
                    'best_R':         best_R,
                    'best_s':         best_s,
                    'best_S':         best_S,
                    'bo_used':               bo_meta['used'],
                    'bo_best_params':        bo_meta['best_params'],
                    'bo_duration':           round(bo_meta['bo_duration'], 2),
                })

            data_all.append({
                    'data':                           data,
                    'first_combined_inventory_level': first_combined_inventory_level,
                    'combined_inventory_level':       combined_inventory_level,
                    'combined_purchases_list':        combined_purchases_list,
                    'combined_sales_list':            combined_sales_list,
                    'first_single_inventory_level':   first_single_inventory_level,
                    'single_inventory_level':         single_inventory_level,
                    'single_purchases_list':          single_purchases_list,
                    'single_sales_list':              single_sales_list,
                    'first_multiple_inventory_data':  first_multiple_inventory_data,
                    'multiple_inventory_data':        multiple_inventory_data,
                    'first_total_order':              sum(i['first_c_order']         for i in data),
                    'first_total_hold':               sum(i['first_c_hold']          for i in data),
                    'first_total_stockout':           sum(i['first_c_stockout']      for i in data),
                    'first_total_all':                sum(i['first_c_total']         for i in data),
                    'first_total_purchases_freq':     sum(i['first_purchases_freq']  for i in data),
                    'first_total_purchases_total':    sum(i['first_purchases_total'] for i in data),
                    'first_total_stockout_total':     sum(i['first_stockout_total']  for i in data),
                    'first_total_calc_duration':      sum(i['first_calc_duration']   for i in data),
                    'total_order':                    sum(i['c_order']            for i in data),
                    'total_hold':                     sum(i['c_hold']             for i in data),
                    'total_stockout':                 sum(i['c_stockout']         for i in data),
                    'total_all':                      sum(i['c_total']            for i in data),
                    'total_purchases_freq':           sum(i['purchases_freq']     for i in data),
                    'total_purchases_total':          sum(i['purchases_total']    for i in data),
                    'total_stockout_total':           sum(i['stockout_total']     for i in data),
                    'total_calc_duration':            sum(i['best_calc_duration'] for i in data),
                })

            total_data = list(total_data_dict.values())

            # ---- Adjust outlet 3 & generate outlet plots --------------- #
            for dt in data_all:
                for inv_key, p_key, s_key in [
                    ('combined_inventory_level', 'combined_purchases_list', 'combined_sales_list'),
                    ('single_inventory_level',   'single_purchases_list',   'single_sales_list'),
                ]:
                    purch_all = [d[p_key] for d in data_all]
                    sales_all = [d[s_key] for d in data_all]
                    if purch_all:
                        total_p = [sum(x) for x in zip(*purch_all)]
                        total_s = [sum(x) for x in zip(*sales_all)]
                        new_inv = []
                        cur     = sum(total_p) - total_s[0]
                        new_inv.append(cur)
                        for sale in total_s[1:]:
                            cur -= sale
                            new_inv.append(cur)
                        dt[inv_key] = new_inv

            total_duration = time.time() - total_start

            context = {
                'data_all':                      data_all,
                'total_data':                    total_data,
                'first_outlet_inventory_levels': first_outlet_inventory_levels,
                'outlet_inventory_levels':       outlet_inventory_levels,
                'first_total_order':             sum(i['first_c_order']         for i in total_data),
                'first_total_hold':              sum(i['first_c_hold']          for i in total_data),
                'first_total_stockout':          sum(i['first_c_stockout']      for i in total_data),
                'first_total_all':               sum(i['first_c_total']         for i in total_data),
                'first_total_calc_duration':     format_seconds(sum(i['first_calc_duration']  for i in total_data)),
                'first_total_purchases_freq':    sum(i['first_purchases_freq']  for i in total_data),
                'first_total_purchases_total':   sum(i['first_purchases_total'] for i in total_data),
                'first_total_stockout_total':    sum(i['first_stockout_total']  for i in total_data),
                'total_order':                   sum(i['c_order']       for i in total_data),
                'total_hold':                    sum(i['c_hold']        for i in total_data),
                'total_stockout':                sum(i['c_stockout']    for i in total_data),
                'total_all':                     sum(i['c_total']       for i in total_data),
                'total_calc_duration':           format_seconds(sum(i['best_calc_duration'] for i in total_data)),
                'total_purchases_freq':          sum(i['purchases_freq']  for i in total_data),
                'total_purchases_total':         sum(i['purchases_total'] for i in total_data),
                'total_stockout_total':          sum(i['stockout_total']  for i in total_data),
                'bo_used':                       use_bo,
                'bo_best_params':                global_bo_params,
                'bo_duration':                   round(bo_duration, 2) if use_bo else 0,
                'total_duration':                format_seconds(total_duration) if total_duration else 0,
            }

            return render(request, 'periodic/calculation_collab.html', context)
    
    context = {
        'data': '',
    }

    return render(request, 'periodic/index.html', context)

BO_BOUNDS = {
    'population_size': (10,   80),
    'crossover_rate':  (0.5,  1.0),
    'mutation_rate':   (0.01, 0.5),
}

# Budget ringan yang dipakai *di dalam* setiap evaluasi BO
BO_INNER_POP   = 5
BO_INNER_GEN   = 5

# Jumlah evaluasi BO
BO_N_CALLS     = 20   # total evaluasi (termasuk n_initial_points)
BO_N_INITIAL   = 5    # titik acak awal sebelum GP mulai memodelkan

# BO_STOCKOUT_WEIGHT = 500.0
BO_STOCKOUT_WEIGHT = 1

# Search space untuk skopt
BO_SPACE = [
    Integer(BO_BOUNDS['population_size'][0], BO_BOUNDS['population_size'][1], name='population_size'),
    Real   (BO_BOUNDS['crossover_rate'][0],  BO_BOUNDS['crossover_rate'][1],  name='crossover_rate'),
    Real   (BO_BOUNDS['mutation_rate'][0],   BO_BOUNDS['mutation_rate'][1],   name='mutation_rate'),
]

def daily_demand(mean, sd, zero_threshold_factor=1.0):
    """Return a stochastic daily demand value (may be 0)."""
    random_num = np.random.uniform(0, 1)
    if random_num < zero_threshold_factor:
        return 0
    return max(0, np.random.normal(mean, sd)) * 2

def simulate_inventory(product):
    product_sim = {k: product[k] for k in product}

    daily_mean = product["permintaan_baku"] / 60
    daily_sd   = product["standar_deviasi"] / np.sqrt(60)

    demand_list  = []
    total_demand = 0

    for _ in range(60):
        d = daily_demand(daily_mean, daily_sd, 0.5)
        if d > 0:
            total_demand += d
        demand_list.append(d)

    product_sim["permintaan_baku"] = round(total_demand)
    product_sim["standar_deviasi"] = np.std(demand_list)

    return product_sim, demand_list

# ---------------------------------------------------------------------------
# Periodic-review analytical formulas
# ---------------------------------------------------------------------------
def per_review(product, demand):
    """EOQ-based periodic-review formula. Returns (total_cost, review_interval)."""
    to = math.sqrt(
        (2 * product["biaya_pesan"]) /
        (product["permintaan_baku"] * product["biaya_simpan"])
    )

    alpha   = to * product["biaya_simpan"] / product["biaya_kekurangan"]
    z_alpha = -NormalDist().inv_cdf(alpha)

    fz_alpha = norm.pdf(2.22, loc=0, scale=1)
    wz_alpha = fz_alpha - 0.00001

    R = (
        product["permintaan_baku"] * to
        + product["permintaan_baku"] * product["lead_time"]
        + z_alpha * math.sqrt(to + product["lead_time"])
    )

    N = math.ceil(
        product["standar_deviasi"]
        * math.sqrt(to + product["lead_time"])
        * -(fz_alpha - z_alpha * wz_alpha)
    )

    T = (
        product["permintaan_baku"] * product["harga_produk"]
        + product["biaya_pesan"] / to
        + product["biaya_simpan"] * (
            R - product["permintaan_baku"] * product["lead_time"]
            + product["permintaan_baku"] * to / 2
        )
        + product["biaya_kekurangan"] / to * N
    )

    return T, to

def find_rss(to, product):
    """Find analytical (R, s, S) values from review interval *to*."""
    r       = product["biaya_simpan"]
    alpha   = to * r / product["biaya_kekurangan"]
    z_alpha = -NormalDist().inv_cdf(alpha)

    fz_alpha = norm.pdf(2.22, loc=0, scale=1)
    wz_alpha = fz_alpha - 0.00001

    R = (
        product["permintaan_baku"] * to
        + product["permintaan_baku"] * product["lead_time"]
        + z_alpha * math.sqrt(to + product["lead_time"])
    )

    N = math.ceil(
        product["standar_deviasi"]
        * math.sqrt(to + product["lead_time"])
        * -(fz_alpha - z_alpha * wz_alpha)
    )

    XR       = to * product["permintaan_baku"]
    XRL      = (to + product["lead_time"]) * product["permintaan_baku"]
    sigma_RL = (to + product["lead_time"]) * product["standar_deviasi"]

    Qp = (
        1.3
        * (XR ** 0.494)
        * ((product["biaya_pesan"] / r) ** 0.506)
        * ((1 + (sigma_RL ** 2) / (XR ** 2)) ** 0.116)
    )
    z  = math.sqrt((Qp * r) / (sigma_RL * product["biaya_kekurangan"]))
    Sp = 0.973 * XRL + sigma_RL * (0.183 / z + 1.063 - 2.192 * z)
    k  = r / (r + product["biaya_kekurangan"])
    So = XRL + k * sigma_RL

    R_to = to * 1000
    s    = Sp
    S    = max(Sp + Qp, So)

    return R_to, s, S

# ---------------------------------------------------------------------------
# Fitness / cost functions
# ---------------------------------------------------------------------------
def min_fitness(product, demand, init_R, init_s, init_S, init_T,
                purchases_freq, tot_lost, stockout_weight=500.0):
    """
    Compute total inventory cost for a given (R, s, S, T) combination.
    Returns (total_cost, total_stockout_units).
    """
    half_demand = demand[:int(init_T)]
    init_R      = max(init_R, 1)

    if purchases_freq <= 0:
        purchases_freq = 1

    tot_demand         = round(sum(half_demand))
    mean_daily_demand  = np.mean(half_demand) if half_demand else 0
    std_dev_monthly    = np.std(half_demand, ddof=1) if len(half_demand) > 1 else 0
    std_dev_daily      = std_dev_monthly / np.sqrt(init_T) if init_T > 0 else 1e-9
    total_daily_demand = round(tot_demand / init_T) if init_T > 0 else 0

    biaya_order = product.get("biaya_order", product.get("biaya_pesan", 0))

    c_order        = biaya_order * (init_T / (purchases_freq * init_R))
    c_hold         = (product["biaya_simpan"] * round((init_S + init_s) / 2)
                      + round((tot_demand * init_R) / purchases_freq))
    total_stockout = round(sum(tot_lost))

    if std_dev_daily > 0:
        def integrand(x):
            return (x - total_daily_demand) * norm.pdf(x, mean_daily_demand, std_dev_daily)
        E_Rv, _ = quad(integrand, total_daily_demand, np.inf)
    else:
        E_Rv = 0.0

    c_stockout = product["biaya_kekurangan"] * E_Rv
    c_total    = c_order + c_hold + c_stockout

    composite = c_total + stockout_weight * total_stockout

    return composite, total_stockout

# ---------------------------------------------------------------------------
# Inventory-level simulators
# ---------------------------------------------------------------------------
def calculate_first_inventory_levels_rss(demand_result, purchases_result):
    """Simulate inventory using actual historical purchase data (no (R,s,S) policy)."""
    inventory_level   = []
    units_lost_list   = []
    total_demand_list = []
    restock_array     = []
    inventory         = 0

    for day in range(len(demand_result)):
        purchase  = purchases_result[day] if day < len(purchases_result) else 0
        demand    = demand_result[day]
        inventory += purchase
        restock_array.append(purchase)

        if inventory >= demand:
            inventory -= demand
            stock_out  = 0
        else:
            stock_out = demand - inventory
            inventory = 0

        inventory_level.append(inventory)
        total_demand_list.append(demand)
        units_lost_list.append(stock_out)

    purchases_freq  = sum(1 for q in restock_array if q > 0)
    purchases_total = sum(restock_array)

    return (inventory_level, total_demand_list, units_lost_list,
            purchases_freq, purchases_total, restock_array)

def calculate_inventory_levels_rss(demand_result, R, s, S):
    """
    Simulate inventory using the (R, s, S) periodic-review policy.
    Review every R days; if stock < s, order up to S after lead_time=1 day.
    Starts with inventory = S (fully stocked).
    """
    inventory_level   = []
    units_lost_list   = []
    total_demand_list = []
    restock_array     = []
    sales_list        = []
    purchases_list    = []

    review_period   = max(int(round(R)), 1)
    lead_time       = 1
    max_inventory   = S
    inventory       = S
    order_placed    = False
    counter         = 0
    purchases_freq  = 0
    purchases_total = 0

    for day, demand in enumerate(demand_result):
        if day % review_period == 0 and not order_placed:
            if inventory < s:
                order_placed = True
                counter      = 0

        if order_placed:
            counter += 1

        if order_placed and counter == lead_time:
            restock_qty      = max(0, max_inventory - inventory)
            inventory       += restock_qty
            restock_array.append(restock_qty)
            purchases_list.append(restock_qty)
            purchases_total += restock_qty
            purchases_freq  += 1
            order_placed     = False
            counter          = 0
        else:
            restock_array.append(0)
            purchases_list.append(0)

        if inventory >= demand:
            inventory -= demand
            stock_out  = 0
            sales      = demand
        else:
            stock_out  = demand - inventory
            sales      = inventory
            inventory  = 0

        inventory_level.append(inventory)
        total_demand_list.append(demand)
        units_lost_list.append(stock_out)
        sales_list.append(sales)

    return (inventory_level, purchases_list, sales_list,
            total_demand_list, units_lost_list,
            max_inventory, purchases_freq, purchases_total, restock_array)

# ---------------------------------------------------------------------------
# Genetic-algorithm operators
# ---------------------------------------------------------------------------
def log_scaled_mutation(individual, mutation_rate, sigma=0.1, lower_bound=1, upper_bound=1000):
    """
    Log-scaled mutation on numeric genes.
    Index 5 (T) is skipped — preserved as an integer choice.
    After mutation, ensures S > s.
    """
    mutated = list(individual)

    for i, gene in enumerate(mutated):
        if i == 5:
            continue
        if not isinstance(gene, (int, float)):
            continue
        if random.random() < mutation_rate:
            r            = random.gauss(0, sigma)
            mutated_gene = gene * (10 ** r)
            mutated[i]   = max(min(mutated_gene, upper_bound), lower_bound)

    _, _, _, temp_s, temp_S, _, _, _ = mutated
    mutated[4] = max(temp_s + 1, temp_S)

    return tuple(mutated)

def fix_S_s(individual):
    """After crossover, guarantee S > s and T is an integer."""
    prod, demand, R, s, S, T, purchases_freq, tot_lost = individual
    S = max(s + 1, S)
    T = int(round(T))
    return (prod, demand, R, s, S, T, purchases_freq, tot_lost)

# ---------------------------------------------------------------------------
# Genetic algorithm  (core)
# ---------------------------------------------------------------------------
def genetic_algorithm(product_data, population_size, num_generations,
        crossover_rate, mutation_rate,
        daily_sales, daily_purchases, stockout_weight=500.0):
    """
    Run a genetic algorithm to minimise total inventory cost for the
    periodic (R, s, S) review policy.

    Returns a fixed 33-element tuple consumed by the view functions.
    """
    # ------------------------------------------------------------------ #
    # Analytical starting point
    # ------------------------------------------------------------------ #
    first_start_time = time.time()

    first_tot_cost, first_to         = per_review(product_data, daily_sales)
    first_R_min, first_s_min, first_S_min = find_rss(first_to, product_data)
    first_R = round(first_R_min)
    first_s = round(first_s_min)
    first_S = round(first_S_min)
    first_T = 60

    (first_inventory_level_list, _, first_tot_lost, first_purchases_freq, first_purchases_total, first_restock_data) = (
        calculate_first_inventory_levels_rss(
            daily_sales[:first_T], daily_purchases[:first_T]
        )
    )

    first_calc_duration = time.time() - first_start_time

    # ------------------------------------------------------------------ #
    # Initial population
    # ------------------------------------------------------------------ #
    population      = []
    variation       = 15
    stock_variation = 5000

    for _ in range(population_size):
        rand_R = random.randint(max(1, first_R - variation), first_R + variation)
        rand_s = random.randint(max(2, first_s - stock_variation), first_s + stock_variation)
        rand_S = random.randint(max(rand_s + 1, first_S), first_S + stock_variation)
        rand_T = int(random.choice([30, 45, 60]))

        (_, _, _, _, pop_tot_lost, _, pop_purchases_freq, _, _) = calculate_inventory_levels_rss(
            daily_sales[:rand_T], rand_R, rand_s, rand_S
        )

        population.append((product_data, daily_sales,
                            rand_R, rand_s, rand_S, rand_T,
                            pop_purchases_freq, pop_tot_lost))

    # ------------------------------------------------------------------ #
    # GA main loop
    # ------------------------------------------------------------------ #
    best_start_time = time.time()
    best_solution   = population[0]

    for generation in range(num_generations):
        fitness_scores = []
        for individual in population:
            prod_sim, demand_res, iR, is_, iS, iT, ipf, itl = individual
            cost, stockout = min_fitness(prod_sim, demand_res, iR, is_, iS, iT, ipf, itl, stockout_weight=stockout_weight)
            fitness_scores.append((cost, stockout))

        if not population:
            break

        best_solution = min(
            zip(population, fitness_scores),
            key=lambda x: (x[1][0], x[1][1])
        )[0]

        # Elitism: carry the best individual forward unchanged
        elite = best_solution

        # Selection (roulette wheel)
        weights = [1.0 / (1.0 + c + s) for c, s in fitness_scores]
        parents = []
        for _ in range(population_size // 2):
            p1 = random.choices(population, weights=weights)[0]
            p2 = random.choices(population, weights=weights)[0]
            parents.append((p1, p2))

        # Crossover
        offspring = []
        for p1, p2 in parents:
            if random.random() < crossover_rate:
                mask   = [random.randint(0, 1) for _ in range(len(p1))]
                child1 = tuple(p1[i] if mask[i] == 0 else p2[i] for i in range(len(p1)))
                child2 = tuple(p2[i] if mask[i] == 0 else p1[i] for i in range(len(p1)))
            else:
                child1, child2 = p1, p2

            child1 = fix_S_s(child1)
            child2 = fix_S_s(child2)
            offspring.extend([child1, child2])

        # Mutation
        offspring = [log_scaled_mutation(ind, mutation_rate) for ind in offspring]

        # Inject elite back into population (replace worst)
        offspring[-1] = elite
        population    = offspring

    # ------------------------------------------------------------------ #
    # Extract best solution
    # ------------------------------------------------------------------ #
    (best_product, best_demand, best_R, best_s, best_S, best_T, best_purchases_freq, best_tot_lost) = best_solution

    best_R = round(best_R)
    best_s = round(best_s)
    best_S = round(best_S)
    best_T = round(best_T)

    best_total_cost, best_to = min_fitness(
        best_product, best_demand,
        best_R, best_s, best_S, best_T,
        best_purchases_freq, best_tot_lost,
        stockout_weight=stockout_weight
    )

    (inventory_level_list, purchases_list, sales_list, tot_dmd, tot_lost, max_inventory, purchases_freq, purchases_total, restock_data) = calculate_inventory_levels_rss(
        best_demand[:best_T], best_R, best_s, best_S
    )

    best_calc_duration = time.time() - best_start_time

    return (
        [], [], [], [], [],
        inventory_level_list, purchases_list, sales_list,
        tot_dmd, tot_lost, max_inventory,
        purchases_freq, purchases_total, restock_data,
        best_product, best_demand,
        best_total_cost, best_to,
        best_R, best_s, best_S, best_T,
        first_R, first_s, first_S, first_T,
        first_purchases_freq, first_tot_lost, daily_sales,
        first_purchases_total,
        first_inventory_level_list, first_restock_data,
        first_calc_duration, best_calc_duration,
    )

def _plot_inventory_level(inventory_level_list, upper_line, x_limit):
    fig, ax = plt.subplots(figsize=(18, 6))
    ax.plot(inventory_level_list, linewidth=1.5)
    ax.axhline(upper_line, linewidth=2, color="grey", linestyle=":")
    ax.axhline(0,          linewidth=2, color="grey", linestyle=":")
    ax.set_xlim(0, x_limit)
    ax.set_ylabel('Inventory Level (pcs)', fontsize=18)
    ax.set_xlabel('Day',                   fontsize=18)
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    buf.close()
    plt.close()
    return encoded

def _plot_stockout_hist(values, label='Stockout'):
    fig, ax = plt.subplots(figsize=(6, 4))
    if values:
        sns.histplot(values, kde=False, color="#097969", ax=ax)
        mean_val = np.mean(values)
        ax.set_title(f'{label} : Mean {mean_val:.3f}')
        ax.axvline(x=mean_val, color='k', alpha=0.5, ls='--')
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    buf.close()
    plt.close()
    return encoded

def _bo_evaluate(params, product_data, daily_sales, daily_purchases, stockout_weight=BO_STOCKOUT_WEIGHT):
    """
    Jalankan GA dengan hyperparameter *params* dan kembalikan composite cost.
    pop_size dan num_generations di-cap ke inner budget agar cepat.
    """
    pop_size, crossover_rate, mutation_rate = params

    pop_size        = max(2, min(int(pop_size), BO_INNER_POP))
    num_generations = BO_INNER_GEN

    try:
        result         = genetic_algorithm(
            product_data, pop_size, num_generations,
            float(crossover_rate), float(mutation_rate),
            daily_sales, daily_purchases,
            stockout_weight=stockout_weight,
        )
        best_total_cost = result[16]
        tot_lost        = result[9]
        total_stockout  = round(sum(tot_lost))
        return float(best_total_cost + stockout_weight * total_stockout)
    except Exception:
        return float('inf')

# ---------------------------------------------------------------------------
# Fungsi utama BO — pengganti pso_optimize_hyperparameters()
# ---------------------------------------------------------------------------
def bo_optimize_hyperparameters(product_data, daily_sales, daily_purchases, n_calls=BO_N_CALLS, n_initial_points=BO_N_INITIAL, stockout_weight=BO_STOCKOUT_WEIGHT, random_state=42):
    """
    Jalankan Bayesian Optimization untuk mencari hyperparameter GA terbaik.

    Parameters
    ----------
    product_data      : dict  — data produk (sama seperti yang dikirim ke GA)
    daily_sales       : list  — penjualan harian
    daily_purchases   : list  — pembelian harian
    n_calls           : int   — total jumlah evaluasi BO
    n_initial_points  : int   — titik acak awal (eksplorasi sebelum GP aktif)
    stockout_weight   : float — bobot penalti stockout
    random_state      : int   — seed untuk reproduksibilitas

    Returns
    -------
    best_params : dict
        Keys: population_size, crossover_rate, mutation_rate
    best_score  : float
        Composite cost terbaik yang ditemukan BO
    history     : list of float
        Skor terbaik (running minimum) di setiap iterasi — untuk plot konvergensi
    """

    # Bungkus evaluator agar menerima list positional args dari gp_minimize
    def objective(params):
        return _bo_evaluate(
            params, product_data, daily_sales, daily_purchases, stockout_weight
        )

    result = gp_minimize(
        func             = objective,
        dimensions       = BO_SPACE,
        n_calls          = n_calls,
        n_initial_points = n_initial_points,
        acq_func         = "EI",          # Expected Improvement
        random_state     = random_state,
        noise            = 1e-10,
    )

    # Running minimum untuk plot konvergensi
    history = []
    running_min = float('inf')
    for val in result.func_vals:
        running_min = min(running_min, val)
        history.append(running_min)

    best_params = {
        'population_size': int(result.x[0]),
        'crossover_rate':  round(float(result.x[1]), 4),
        'mutation_rate':   round(float(result.x[2]), 4),
    }

    return best_params, float(result.fun), history

# ---------------------------------------------------------------------------
# Versi global (multi-produk) — pengganti pso_optimize_hyperparameters_global()
# ---------------------------------------------------------------------------
def bo_optimize_hyperparameters_global(products_data,
                                        num_generations=50,
                                        n_calls=BO_N_CALLS,
                                        n_initial_points=BO_N_INITIAL,
                                        stockout_weight=BO_STOCKOUT_WEIGHT,
                                        random_state=42):
    """
    Cari hyperparameter GA terbaik yang berlaku untuk SEMUA produk sekaligus.
    Fitness = rata-rata composite cost di seluruh produk.

    products_data : list of (product_dict, daily_sales, daily_purchases)
    """

    def objective(params):
        scores = []
        for product_data, daily_sales, daily_purchases in products_data:
            s = _bo_evaluate(params, product_data, daily_sales, daily_purchases, stockout_weight)
            if s < float('inf'):
                scores.append(s)
        # Kembalikan rata-rata; jika semua gagal, kembalikan penalti besar
        return float(np.mean(scores)) if scores else float('inf')

    result = gp_minimize(
        func             = objective,
        dimensions       = BO_SPACE,
        n_calls          = n_calls,
        n_initial_points = n_initial_points,
        acq_func         = "EI",
        random_state     = random_state,
        noise            = 1e-10,
    )

    history = []
    running_min = float('inf')
    for val in result.func_vals:
        running_min = min(running_min, val)
        history.append(running_min)

    best_params = {
        'population_size': int(result.x[0]),
        'crossover_rate':  round(float(result.x[1]), 4),
        'mutation_rate':   round(float(result.x[2]), 4),
    }

    return best_params, float(result.fun), history

# ---------------------------------------------------------------------------
# Convenience wrapper — pengganti run_with_pso()
# ---------------------------------------------------------------------------
def run_with_bo(product_data, daily_sales, daily_purchases,
                user_pop_size, user_num_gen, user_cr, user_mr,
                use_bo=True,
                bo_n_calls=BO_N_CALLS,
                bo_n_initial=BO_N_INITIAL,
                stockout_weight=BO_STOCKOUT_WEIGHT):
    """
    Drop-in replacement untuk run_with_pso().

    Jika use_bo=True:
        1. Jalankan BO untuk cari hyperparameter optimal (budget ringan).
        2. Jalankan final GA dengan hyperparameter terbaik + budget user.
        3. Return GA result tuple + bo_meta dict.

    Jika use_bo=False:
        Langsung jalankan GA dengan hyperparameter dari user.
    """
    bo_meta = {
        'used':         use_bo,
        'best_params':  None,
        'best_score':   None,
        'history':      [],
        'bo_duration':  0.0,
    }

    if use_bo:
        bo_start = time.time()

        best_params, best_score, history = bo_optimize_hyperparameters(
            product_data, daily_sales, daily_purchases,
            n_calls         = bo_n_calls,
            n_initial_points= bo_n_initial,
            stockout_weight = stockout_weight,
        )

        bo_meta['best_params'] = best_params
        bo_meta['best_score']  = best_score
        bo_meta['history']     = history
        bo_meta['bo_duration'] = time.time() - bo_start

        # Ambil nilai terbesar antara saran BO dan input user
        final_pop = max(best_params['population_size'], user_pop_size)
        final_gen = user_num_gen        # BO tidak mengoptimasi num_generations
        final_cr  = best_params['crossover_rate']
        final_mr  = best_params['mutation_rate']
    else:
        final_pop = user_pop_size
        final_gen = user_num_gen
        final_cr  = user_cr
        final_mr  = user_mr

    ga_result = genetic_algorithm(
        product_data, final_pop, final_gen, final_cr, final_mr,
        daily_sales, daily_purchases,
        stockout_weight=stockout_weight,
    )

    return ga_result, bo_meta
# ---------------------------------------------------------------------------
# Plot helper — pengganti _plot_pso_convergence()
# ---------------------------------------------------------------------------
def _plot_bo_convergence(history):
    """
    Return base64-encoded PNG dari kurva konvergensi BO.
    history adalah list running-minimum score per iterasi.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(history, linewidth=1.8, color="#1a6faf", marker='o', markersize=3)
    ax.set_xlabel('BO Iteration', fontsize=13)
    ax.set_ylabel('Best Composite Cost', fontsize=13)
    ax.set_title('Bayesian Optimization Convergence — Hyperparameter Tuning', fontsize=14)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x):,}'))
    ax.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    return encoded

def _parse_post_float(post, key, default):
    """Read a float from POST data, falling back to default if blank or invalid."""
    val = post.get(key, '').strip()
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def _parse_post_int(post, key, default):
    """Read an int from POST data, falling back to default if blank or invalid."""
    val = post.get(key, '').strip()
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def format_seconds(seconds):
    return str(timedelta(seconds=round(seconds)))

# PSO Helper Methods
import math
import random
import numpy as np


class Particle:
    def __init__(self, bounds):
        self.position = [
            random.uniform(lower, upper)
            for lower, upper in bounds
        ]

        self.velocity = [
            random.uniform(-(upper - lower), upper - lower) * 0.1
            for lower, upper in bounds
        ]

        self.best_pos = list(self.position)
        self.best_score = float('inf')
        self.score = float('inf')

    def evaluate(self, cost_func):
        self.score = cost_func(self.position)

        if self.score < self.best_score:
            self.best_score = self.score
            self.best_pos = list(self.position)

    def update_velocity(self, global_best_pos, w, c1=1.5, c2=1.5):
        for i in range(len(self.position)):
            r1 = random.random()
            r2 = random.random()

            cognitive = c1 * r1 * (self.best_pos[i] - self.position[i])
            social = c2 * r2 * (global_best_pos[i] - self.position[i])

            self.velocity[i] = (w * self.velocity[i]) + cognitive + social

    def update_position(self, bounds):
        for i in range(len(self.position)):
            lower, upper = bounds[i]

            self.position[i] += self.velocity[i]
            self.position[i] = max(lower, min(upper, self.position[i]))


def run_pso(cost_func, bounds, num_particles=40, maxiter=100, w_start=0.9, w_end=0.4):
    particles = [Particle(bounds) for _ in range(num_particles)]

    global_best_pos = None
    global_best_score = float('inf')

    for iteration in range(maxiter):
        w = w_start - ((w_start - w_end) * iteration / maxiter)

        for particle in particles:
            particle.evaluate(cost_func)

            if particle.score < global_best_score:
                global_best_score = particle.score
                global_best_pos = list(particle.position)

        for particle in particles:
            particle.update_velocity(global_best_pos, w)
            particle.update_position(bounds)

    return global_best_pos, global_best_score

# Kalkulasi simulasi biaya inventory PSO
def simulate_inventory_rss(
    demand_list,
    R,
    s,
    S,
    lead_time_days,
    ordering_cost,
    holding_cost_per_unit_per_day,
    shortage_cost_per_unit,
    initial_stock=None,
):
    R = max(1, int(round(R)))
    s = max(0, int(round(s)))
    S = max(s + 1, int(round(S)))
    lead_time_days = max(0, int(round(lead_time_days)))

    if initial_stock is None:
        stock_on_hand = S
    else:
        stock_on_hand = max(0, int(round(initial_stock)))

    pending_orders = []

    total_ordering_cost = 0
    total_holding_cost = 0
    total_shortage_cost = 0
    total_stockout_qty = 0
    total_order_qty = 0
    order_count = 0

    stock_history = []
    stockout_history = []
    order_history = []

    for day_index, demand in enumerate(demand_list, start=1):
        demand = max(0, float(demand))

        # 1. Terima pesanan yang jatuh tempo hari ini
        arrived_orders = [
            order for order in pending_orders
            if order['arrival_day'] == day_index
        ]

        for order in arrived_orders:
            stock_on_hand += order['qty']

        pending_orders = [
            order for order in pending_orders
            if order['arrival_day'] > day_index
        ]

        # 2. Penuhi demand
        if stock_on_hand >= demand:
            stock_on_hand -= demand
            stockout_qty = 0
        else:
            stockout_qty = demand - stock_on_hand
            stock_on_hand = 0

        total_stockout_qty += stockout_qty
        total_shortage_cost += stockout_qty * shortage_cost_per_unit

        # 3. Hitung holding cost berdasarkan stok akhir hari
        total_holding_cost += stock_on_hand * holding_cost_per_unit_per_day

        # 4. Review setiap R hari
        order_qty = 0

        if day_index % R == 0:
            on_order_qty = sum(order['qty'] for order in pending_orders)
            inventory_position = stock_on_hand + on_order_qty

            if inventory_position <= s:
                order_qty = S - inventory_position
                order_qty = max(0, order_qty)

                if order_qty > 0:
                    arrival_day = day_index + lead_time_days

                    pending_orders.append({
                        'arrival_day': arrival_day,
                        'qty': order_qty,
                    })

                    total_ordering_cost += ordering_cost
                    total_order_qty += order_qty
                    order_count += 1

        stock_history.append(stock_on_hand)
        stockout_history.append(stockout_qty)
        order_history.append(order_qty)

    total_inventory_cost = (
        total_ordering_cost
        + total_holding_cost
        + total_shortage_cost
    )

    return {
        'total_inventory_cost': total_inventory_cost,
        'ordering_cost': total_ordering_cost,
        'holding_cost': total_holding_cost,
        'shortage_cost': total_shortage_cost,
        'total_stockout_qty': total_stockout_qty,
        'total_order_qty': total_order_qty,
        'order_count': order_count,
        'average_stock': np.mean(stock_history) if stock_history else 0,
        'stock_history': stock_history,
        'stockout_history': stockout_history,
        'order_history': order_history,
    }

# Cari RsS optimal PSO
def find_optimal_rss_pso(
    demand_list,
    lead_time_days,
    ordering_cost,
    holding_cost_per_unit_per_day,
    shortage_cost_per_unit,
    min_R=1,
    max_R=30,
    min_s=0,
    max_s=None,
    min_S=1,
    max_S=None,
    num_particles=40,
    maxiter=100,
):
    total_demand = sum(demand_list)
    mean_demand = np.mean(demand_list) if demand_list else 0

    if max_s is None:
        max_s = max(10, int(total_demand))

    if max_S is None:
        max_S = max(20, int(total_demand * 1.5))

    bounds = [
        (min_R, max_R),   # R
        (min_s, max_s),   # s
        (min_S, max_S),   # S
    ]

    def cost_function(position):
        R = int(round(position[0]))
        s = int(round(position[1]))
        S = int(round(position[2]))

        # Constraint: S harus lebih besar dari s
        if S <= s:
            return float('inf')

        result = simulate_inventory_rss(
            demand_list=demand_list,
            R=R,
            s=s,
            S=S,
            lead_time_days=lead_time_days,
            ordering_cost=ordering_cost,
            holding_cost_per_unit_per_day=holding_cost_per_unit_per_day,
            shortage_cost_per_unit=shortage_cost_per_unit,
            initial_stock=S,
        )

        return result['total_inventory_cost']

    best_pos, best_score = run_pso(
        cost_func=cost_function,
        bounds=bounds,
        num_particles=num_particles,
        maxiter=maxiter,
    )

    best_R = int(round(best_pos[0]))
    best_s = int(round(best_pos[1]))
    best_S = int(round(best_pos[2]))

    if best_S <= best_s:
        best_S = best_s + 1

    best_result = simulate_inventory_rss(
        demand_list=demand_list,
        R=best_R,
        s=best_s,
        S=best_S,
        lead_time_days=lead_time_days,
        ordering_cost=ordering_cost,
        holding_cost_per_unit_per_day=holding_cost_per_unit_per_day,
        shortage_cost_per_unit=shortage_cost_per_unit,
        initial_stock=best_S,
    )

    return {
        'R': best_R,
        's': best_s,
        'S': best_S,
        'cost': best_result['total_inventory_cost'],
        'result': best_result,
    }

# ==============================================================================
# NORMAL DISTRIBUTION HELPER
# ==============================================================================

def normal_pdf(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def normal_cdf(z):
    return NormalDist().cdf(z)


def normal_loss_function(z):
    """
    L(z) = f(z) - z * (1 - F(z))
    """
    return normal_pdf(z) - z * (1 - normal_cdf(z))


# ==============================================================================
# HADLEY-WHITIN / PERIODIC REVIEW
# ==============================================================================

def find_initial_to(A, D, h):
    """
    T0 = sqrt(2A / (D*h))

    T0 di sini adalah fraksi periode, bukan hari langsung.
    """
    D = max(float(D), 1e-9)
    h = max(float(h), 1e-9)
    A = max(float(A), 0)

    return math.sqrt((2 * A) / (D * h))


def calculate_periodic_review_hadley(
    to,
    D,
    A,
    h,
    Cu,
    P,
    L,
    sigma,
    include_purchase_cost=False,
):
    """
    Mengikuti struktur rumus referensi:

    OT = D*P + A/To + h(R - D*L + D*To/2) + (Cu/To)*N

    Keterangan:
    to    = T0 / review interval dalam fraksi periode
    D     = total demand selama periode perencanaan
    A     = biaya pesan per order
    h     = biaya simpan per unit per periode
    Cu    = biaya kekurangan per unit
    P     = harga material/barang per unit
    L     = lead time dalam fraksi periode
    sigma = standar deviasi demand selama periode
    """

    to = max(float(to), 1e-9)
    D = max(float(D), 0)
    A = max(float(A), 0)
    h = max(float(h), 0)
    Cu = max(float(Cu), 1e-9)
    P = max(float(P), 0)
    L = max(float(L), 0)
    sigma = max(float(sigma), 0)

    # alpha = To * h / Cu
    alpha = (to * h) / Cu
    alpha = max(1e-6, min(1 - 1e-6, alpha))

    # Referensi memakai z alpha positif.
    # Kalau alpha kecil 0.0134, z sekitar 2.2
    z_alpha = NormalDist().inv_cdf(1 - alpha)

    fz = normal_pdf(z_alpha)
    psi = 1 - normal_cdf(z_alpha)
    loss = normal_loss_function(z_alpha)

    protection_period = to + L
    sigma_protection = sigma * math.sqrt(protection_period)

    safety_stock = z_alpha * sigma_protection

    # Reorder level / R dalam unit barang
    reorder_level = (D * to) + (D * L) + safety_stock

    # Expected shortage
    N = sigma_protection * loss
    N = max(0, N)

    purchase_cost = D * P if include_purchase_cost else 0
    ordering_cost = A / to
    holding_cost = h * (reorder_level - (D * L) + ((D * to) / 2))
    shortage_cost = (Cu / to) * N

    inventory_cost = ordering_cost + holding_cost + shortage_cost
    total_cost = purchase_cost + inventory_cost

    return {
        'to': to,
        'alpha': alpha,
        'z_alpha': z_alpha,
        'fz': fz,
        'psi': psi,
        'loss': loss,

        'protection_period': protection_period,
        'sigma_protection': sigma_protection,
        'safety_stock': safety_stock,
        'reorder_level': reorder_level,
        'N': N,

        'purchase_cost': purchase_cost,
        'ordering_cost': ordering_cost,
        'holding_cost': holding_cost,
        'shortage_cost': shortage_cost,

        'inventory_cost': inventory_cost,
        'total_cost': total_cost,
    }


def calculate_s_s_policy(to, D, A, h, Cu, L, sigma):
    """
    Mengikuti pendekatan parameter (s, S) dari referensi.

    XR     = R * D
    XRL    = (R + L) * D
    sigmaRL = sigma * sqrt(R + L)
    """

    to = max(float(to), 1e-9)
    D = max(float(D), 0)
    A = max(float(A), 0)
    h = max(float(h), 1e-9)
    Cu = max(float(Cu), 1e-9)
    L = max(float(L), 0)
    sigma = max(float(sigma), 0)

    XR = to * D
    XRL = (to + L) * D
    sigma_RL = sigma * math.sqrt(to + L)

    XR_safe = max(XR, 1e-9)
    sigma_safe = max(sigma_RL, 1e-9)

    # Di referensi tertulis A/(v*r), tapi contoh angkanya memakai A/h.
    # Jadi kalau h kamu sudah berupa biaya simpan Rupiah/unit/periode, pakai A/h.
    Qp = (
        1.3
        * (XR_safe ** 0.494)
        * ((A / h) ** 0.506)
        * ((1 + ((sigma_safe ** 2) / (XR_safe ** 2))) ** 0.116)
    )

    Qp = max(1, Qp)

    z_sp = math.sqrt(max(0, (Qp * h) / (sigma_safe * Cu)))

    if z_sp <= 0:
        Sp = (0.973 * XRL) + (sigma_RL * (1.063))
    else:
        Sp = (
            (0.973 * XRL)
            + sigma_RL * ((0.183 / z_sp) + 1.063 - (2.192 * z_sp))
        )

    # Sesuai referensi:
    # k = h / (h + Cu)
    k = h / (h + Cu)
    S0 = XRL + (k * sigma_RL)

    s = min(Sp, S0)
    S = min(Sp + Qp, S0)

    # Safety guard supaya S tidak lebih kecil dari s
    if S <= s:
        S = s + Qp

    return {
        'XR': XR,
        'XRL': XRL,
        'sigma_RL': sigma_RL,
        'Qp': Qp,
        'z_sp': z_sp,
        'Sp': Sp,
        'k': k,
        'S0': S0,
        's': s,
        'S': S,
    }


def find_optimal_to_pso(
    D,
    A,
    h,
    Cu,
    P,
    L,
    sigma,
    period_days,
    min_days=1,
    max_days=30,
    include_purchase_cost=False,
    num_particles=40,
    maxiter=100,
):
    """
    PSO mencari To optimal.

    Bounds PSO tetap dalam fraksi periode:
    min_to = min_days / period_days
    max_to = max_days / period_days
    """

    period_days = max(int(period_days), 1)

    min_to = max(1e-6, min_days / period_days)
    max_to = max(min_to + 1e-6, max_days / period_days)

    def cost_function(position):
        to = position[0]

        result = calculate_periodic_review_hadley(
            to=to,
            D=D,
            A=A,
            h=h,
            Cu=Cu,
            P=P,
            L=L,
            sigma=sigma,
            include_purchase_cost=include_purchase_cost,
        )

        # Untuk optimasi, sebaiknya pakai inventory_cost saja.
        # purchase_cost D*P konstan dan tidak memengaruhi To.
        return result['inventory_cost']

    best_pos, best_score = run_pso(
        cost_function,
        bounds=[(min_to, max_to)],
        num_particles=num_particles,
        maxiter=maxiter,
    )

    return best_pos[0], best_score


def to_to_days(to, period_days):
    return max(1, round(to * period_days))


def days_to_to(days, period_days):
    return max(1, days) / max(1, period_days)