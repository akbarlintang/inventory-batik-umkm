from __future__ import division

from django.shortcuts import render
from django.http import Http404
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
from django.core import serializers
import json
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
# from decorators import anonymous_required
from django.contrib.auth.decorators import login_required

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

from django.shortcuts import redirect

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
            return render(request, 'login.html', {'error': 'Username tidak ditemukan'})

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
    purchases       = Purchase.objects.all()
    sales           = Sales.objects.all()
    products        = Item.objects.filter(type="JADI")
    outlets         = Outlet.objects.all()

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
    # Ambil tanggal awal bulan ini
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Ambil tanggal awal bulan berikutnya
    start_of_next_month = (start_of_month + timedelta(days=32)).replace(day=1)

    # Filter data penjualan hanya untuk bulan ini
    sales = Sales.objects.filter(created_at__gte=start_of_month, created_at__lt=start_of_next_month)

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
    outlets = Outlet.objects.all()
    context = {
        'outlets': outlets
    }

    return render(request, 'outlet/index.html', context)

@login_required
def outlet_create_view(request):
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    if request.method == 'POST':
        # membuat objek dari class TaskForm
        form = OutletForm(request.POST)
        # Mengecek validasi form
        if form.is_valid():
            # Membuat Task baru dengan data yang disubmit
            new_task = OutletForm(request.POST)
            # Simpan data ke dalam table tasks
            new_task.save()
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
    outlets = Outlet.objects.all()
    data = serializers.serialize('json', outlets)
    
    return HttpResponse(data, content_type="text/json-comment-filtered")

# Material
@login_required
def material_view(request):
    materials = Material.objects.all()
    context = {
        'materials': materials
    }

    return render(request, 'material/index.html', context)

@login_required
def material_create_view(request):
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    if request.method == 'POST':
        # membuat objek dari class TaskForm
        form = MaterialForm(request.POST, request.FILES)
        # Mengecek validasi form
        if form.is_valid():
            # Membuat Task baru dengan data yang disubmit
            new_task = MaterialForm(request.POST, request.FILES)
            # Simpan data ke dalam table tasks
            new_task.save()
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
    items = Item.objects.filter(type="JADI")
    context = {
        'items': items
    }

    return render(request, 'product/index.html', context)

def product_create_view(request):
    # Mengecek method pada request
    # Jika method-nya adalah POST, maka akan dijalankan
    # proses validasi dan penyimpanan data
    if request.method == 'POST':
        # membuat objek dari class TaskForm
        form = ItemForm(request.POST, request.FILES)
        # Mengecek validasi form
        if form.is_valid():
            # Membuat Task baru dengan data yang disubmit
            new_task = ItemForm(request.POST, request.FILES)
            # Simpan data ke dalam table tasks
            new_task.save()
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
        form = RecipeForm(request.POST, request.FILES)
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
        form = RecipeForm()
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
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            purchases = Purchase.objects.all().order_by('-created_at')
        else:
            purchases = Purchase.objects.filter(outlet_id=request.session['outlet_id']).order_by('-created_at')
    else:
        purchases = Purchase.objects.all()

    context = {
        'purchases': purchases
    }

    return render(request, 'purchase/index.html', context)

@login_required
def purchase_create_view(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            temp = form.save()

            # Simpan transaction dari purchase
            Transaction.objects.create(
                item_id = request.POST.get('item',''),
                outlet_id = request.POST.get('outlet',''),
                purchase_id = temp.id,
                type = 'purchase'
            )

            messages.success(request, 'Sukses menambah pembelian baru.')
            return redirect('purchase.index')
    else:
        form = PurchaseForm()
    return render(request, 'purchase/form.html', {'form': form})

@login_required
def purchase_update_view(request, purchase_id):
    try:
        purchase = Purchase.objects.get(pk=purchase_id)
    except Purchase.DoesNotExist:
        raise Http404("Pembelian tidak ditemukan.")
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sukses Mengubah pembelian.')
            return redirect('purchase.index')
    else:
        form = PurchaseForm(instance=purchase)
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
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            productions = Production.objects.all().order_by('-created_at')
        else:
            productions = Production.objects.filter(outlet_id=request.session['outlet_id']).order_by('-created_at')
    else:
        productions = Production.objects.all()

    context = {
        'productions': productions
    }

    return render(request, 'production/index.html', context)

@login_required
def production_create_view(request):
    if request.method == 'POST':
        form = ProductionForm(request.POST)
        if form.is_valid():
            form.save()

            # Simpan stock dari production
            try:
                obj = Stock.objects.get(outlet=request.POST.get('outlet',''), item=request.POST.get('item',''))
                obj.amount = int(obj.amount) + int(request.POST.get('amount',''))
                obj.save()
            except Stock.DoesNotExist:
                Stock.objects.create(
                    item_id = request.POST.get('item',''),
                    outlet_id = request.POST.get('outlet',''),
                    amount = request.POST.get('amount',''),
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
        form = ProductionForm(request.POST, instance=production)
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
                    amount = request.POST.get('amount',''),
                )
            
            messages.success(request, 'Sukses Mengubah Produksi.')
            return redirect('production.index')
    else:
        form = ProductionForm(instance=production)
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
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            sales = Sales.objects.all().order_by('-created_at')
        else:
            sales = Sales.objects.filter(outlet_id=request.session['outlet_id']).order_by('-created_at')
    else:
        sales = Sales.objects.all()

    context = {
        'sales': sales
    }

    return render(request, 'sales/index.html', context)

@login_required
def sales_create_view(request):
    if request.method == 'POST':
        form = SalesForm(request.POST)
        if form.is_valid():
            temp = form.save()

            # Simpan transaction dari sales
            Transaction.objects.create(
                item_id = request.POST.get('item',''),
                outlet_id = request.POST.get('outlet',''),
                sales_id = temp.id,
                type = 'sales'
            )

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
                )

            messages.success(request, 'Sukses menambah penjualan baru.')
            return redirect('sales.index')
    else:
        form = SalesForm()
    return render(request, 'sales/form.html', {'form': form})

@login_required
def sales_update_view(request, sales_id):
    try:
        sales = Sales.objects.get(pk=sales_id)
    except Sales.DoesNotExist:
        raise Http404("Penjualan tidak ditemukan.")
    if request.method == 'POST':
        form = SalesForm(request.POST, instance=sales)
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
                )

            messages.success(request, 'Sukses Mengubah penjualan.')
            return redirect('sales.index')
    else:
        form = SalesForm(instance=sales)
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
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            transactions = Transaction.objects.all().order_by('-created_at')
        else:
            transactions = Transaction.objects.filter(outlet_id=request.session['outlet_id']).order_by('-created_at')
    else:
        transactions = Transaction.objects.all()
    
    context = {
        'transactions': transactions
    }

    return render(request, 'transaction/index.html', context)

# Stocks
@login_required
def stock_view(request):
    if request.session.has_key('outlet_id'):
        if request.session['outlet_id'] == 'all':
            stocks = Stock.objects.all()
        else:
            stocks = Stock.objects.filter(outlet_id=request.session['outlet_id'])
    else:
        stocks = Stock.objects.all()
    
    context = {
        'stocks': stocks
    }

    return render(request, 'stock/index.html', context)

# Export
@login_required
def export_view(request):
    if request.method == 'POST':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ExportData.csv"'        
        writer = csv.writer(response)
        writer.writerow(['Sales Data'])
        writer.writerow(['No', 'Nama Barang','Biaya Pesan','Permintaan Bahan Baku','Biaya Simpan','Biaya Kekurangan','Harga Produk','Lead Time Pemenuhan', 'Standar Deviasi'])
        items = Item.objects.filter(type="JADI").all()
        for idx, item in enumerate(items):
            sales = Sales.objects.all().filter(item_id=item.id)

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

    # Mencari total biaya pesan
    biaya_pesan = (A * D) / Q

    # Mencari total biaya simpan
    biaya_simpan = ((Q / 2) + (k * sigma_RL) * vr)

    # Mencari total biaya kekurangan
    biaya_kekurangan = (B3 * sigma_RL * 0.216 * D) / Q

    # Hitung ongkos total dan masukkan ke dalam list
    ongkos_total = biaya_pesan + biaya_simpan + biaya_kekurangan
    
    return ongkos_total

def periodic_view(request):
    if request.method == 'POST':
        array = []
        data = []

        read_file = request.FILES['file']
        csv_data = pd.read_csv(read_file, header=1, encoding="UTF-8")

        for dt in csv_data.values:
            array_data = {}
            array_data['nama_barang'] = dt[1]
            array_data['biaya_pesan'] = dt[2]
            array_data['permintaan_baku'] = dt[3]
            array_data['biaya_simpan'] = dt[4]
            array_data['biaya_kekurangan'] = dt[5]
            array_data['harga_material'] = dt[6]
            array_data['lead_time'] = dt[7] / 100
            array_data['standar_deviasi'] = dt[8]

            array.append(array_data)

        for x in array:
            nama_barang = x['nama_barang']
            biaya_pesan = x['biaya_pesan']
            permintaan_baku = x['permintaan_baku']
            biaya_simpan = x['biaya_simpan']
            biaya_kekurangan = x['biaya_kekurangan']
            harga_material = x['harga_material']
            lead_time = x['lead_time']
            standar_deviasi = x['standar_deviasi']
            
            class Particle:
                def __init__(self,x0):
                    self.position_i=[]          # particle position
                    self.velocity_i=[]          # particle velocity
                    self.pos_best_i=[]          # best position individual
                    self.err_best_i=-1          # best error individual
                    self.err_i=-1               # error individual

                    for i in range(0,num_dimensions):
                        self.velocity_i.append(random.uniform(-1,1))
                        self.position_i.append(x0[i])

                # evaluate current fitness
                def evaluate(self,costFunc):
                    self.err_i=costFunc(self.position_i)

                    # check to see if the current position is an individual best
                    if self.err_i < self.err_best_i or self.err_best_i==-1:
                        self.pos_best_i=self.position_i
                        self.err_best_i=self.err_i

                # update new particle velocity
                def update_velocity(self,pos_best_g):
                    w=0.5       # constant inertia weight (how much to weigh the previous velocity)
                    c1=1        # cognative constant
                    c2=2        # social constant

                    for i in range(0,num_dimensions):
                        r1=random.random()
                        r2=random.random()

                        vel_cognitive=c1*r1*(self.pos_best_i[i]-self.position_i[i])
                        vel_social=c2*r2*(pos_best_g[i]-self.position_i[i])
                        self.velocity_i[i]=w*self.velocity_i[i]+vel_cognitive+vel_social

                # update the particle position based off new velocity updates
                def update_position(self,bounds):
                    for i in range(0,num_dimensions):
                        self.position_i[i]=self.position_i[i]+self.velocity_i[i]

                        # adjust maximum position if necessary
                        if self.position_i[i]>bounds[i][1]:
                            self.position_i[i]=bounds[i][1]

                        # adjust minimum position if neseccary
                        if self.position_i[i] < bounds[i][0]:
                            self.position_i[i]=bounds[i][0]

            class PSO():
                def __new__(self,costFunc,x0,bounds,num_particles,maxiter):
                    global num_dimensions

                    num_dimensions=len(x0)
                    err_best_g=-1                   # best error for group
                    pos_best_g=[]                   # best position for group

                    # establish the swarm
                    swarm=[]
                    for i in range(0,num_particles):
                        swarm.append(Particle(x0))

                    # begin optimization loop
                    i=0
                    while i < maxiter:
                        #print i,err_best_g
                        # cycle through particles in swarm and evaluate fitness
                        for j in range(0,num_particles):
                            swarm[j].evaluate(costFunc)

                            # determine if current particle is the best (globally)
                            if swarm[j].err_i < err_best_g or err_best_g == -1:
                                pos_best_g=list(swarm[j].position_i)
                                err_best_g=float(swarm[j].err_i)

                        # cycle through swarm and update velocities and position
                        for j in range(0,num_particles):
                            swarm[j].update_velocity(pos_best_g)
                            swarm[j].update_position(bounds)
                        i+=1

                    # print final results
                    # print ('FINAL:')
                    # print (pos_best_g)
                    # print (err_best_g)

                    return err_best_g
            
            def func1(x):
                # Hitung nilai To
                to = math.sqrt((2 * biaya_pesan) / (permintaan_baku * biaya_simpan))

                # To = round(to * 100)

                return to

            def func2(x):
                T_temp = []
                To_temp = []
                s_temp = []
                S_temp = []
                for i in range(5):
                    # Hitung nilai To
                    to = math.sqrt((2 * biaya_pesan) / (permintaan_baku * biaya_simpan))

                    if i == 0:
                        to = to - 0.002
                    elif i == 1:
                        to = to - 0.001
                    elif i == 3:
                        to = to + 0.001
                    elif i == 4:
                        to = to + 0.002

                    # Hitung nilai alpha dan R
                    alpha = to * biaya_simpan / biaya_kekurangan
                    z_alpha = round((NormalDist().inv_cdf(alpha) * -1), 2)

                    fz_alpha = round(norm.pdf(2.22 , loc = 0 , scale = 1 ), 5)
                    # wz_alpha = fz_alpha - (z_alpha * (1 - fz_alpha))
                    wz_alpha = round((fz_alpha - 0.00001), 5)

                    R = round((permintaan_baku * to) + (permintaan_baku * lead_time) + (z_alpha * (math.sqrt(to + lead_time))))

                    # Hitung total biaya total persediaan
                    N = math.ceil(standar_deviasi * ((math.sqrt(to + lead_time)) * ((fz_alpha - (z_alpha * wz_alpha)) * -1)))

                    T = (permintaan_baku * harga_material) + (biaya_pesan / to) + (biaya_simpan * (R - (permintaan_baku * lead_time) + (permintaan_baku * to / 2))) + (biaya_kekurangan / to * N)

                    # Hitung nilai XR, XRL, dan sigma_RL
                    XR = to * permintaan_baku
                    XRL = (to + lead_time) * permintaan_baku
                    sigma_RL = (to + lead_time) * standar_deviasi

                    Qp = round(1.3 * (XR ** 0.494) * ((biaya_pesan / biaya_simpan) ** 0.506) * ((1 + ((sigma_RL ** 2) / (XR ** 2))) ** 0.116))
                    z = round(math.sqrt((Qp * biaya_simpan) / (sigma_RL * biaya_kekurangan)), 2)
                    Sp = round((0.973 * XRL) + (sigma_RL * ((0.183 / z) + 1.063 - (2.192 * z))), 2)

                    k = round(biaya_simpan / (biaya_simpan + biaya_kekurangan), 2)

                    So = round(XRL + (k * sigma_RL))

                    To = round(to * 100)
                    s = round(Qp)
                    S = round(Sp + Qp)

                    T_temp.append(T)
                    To_temp.append(To)
                    s_temp.append(s)
                    S_temp.append(S)
                
                for idx, temp in enumerate(T_temp):
                    if temp == min(T_temp):
                        index = idx
                        break

                return s_temp[index]
            
            def func3(x):
                T_temp = []
                To_temp = []
                s_temp = []
                S_temp = []
                for i in range(5):
                    # Hitung nilai To
                    to = math.sqrt((2 * biaya_pesan) / (permintaan_baku * biaya_simpan))

                    if i == 0:
                        to = to - 0.002
                    elif i == 1:
                        to = to - 0.001
                    elif i == 3:
                        to = to + 0.001
                    elif i == 4:
                        to = to + 0.002

                    # Hitung nilai alpha dan R
                    alpha = to * biaya_simpan / biaya_kekurangan
                    z_alpha = round((NormalDist().inv_cdf(alpha) * -1), 2)

                    fz_alpha = round(norm.pdf(2.22 , loc = 0 , scale = 1 ), 5)
                    # wz_alpha = fz_alpha - (z_alpha * (1 - fz_alpha))
                    wz_alpha = round((fz_alpha - 0.00001), 5)

                    R = round((permintaan_baku * to) + (permintaan_baku * lead_time) + (z_alpha * (math.sqrt(to + lead_time))))

                    # Hitung total biaya total persediaan
                    N = math.ceil(standar_deviasi * ((math.sqrt(to + lead_time)) * ((fz_alpha - (z_alpha * wz_alpha)) * -1)))

                    T = (permintaan_baku * harga_material) + (biaya_pesan / to) + (biaya_simpan * (R - (permintaan_baku * lead_time) + (permintaan_baku * to / 2))) + (biaya_kekurangan / to * N)

                    # Hitung nilai XR, XRL, dan sigma_RL
                    XR = to * permintaan_baku
                    XRL = (to + lead_time) * permintaan_baku
                    sigma_RL = (to + lead_time) * standar_deviasi

                    Qp = round(1.3 * (XR ** 0.494) * ((biaya_pesan / biaya_simpan) ** 0.506) * ((1 + ((sigma_RL ** 2) / (XR ** 2))) ** 0.116))
                    z = round(math.sqrt((Qp * biaya_simpan) / (sigma_RL * biaya_kekurangan)), 2)
                    Sp = round((0.973 * XRL) + (sigma_RL * ((0.183 / z) + 1.063 - (2.192 * z))), 2)

                    k = round(biaya_simpan / (biaya_simpan + biaya_kekurangan), 2)

                    So = round(XRL + (k * sigma_RL))

                    To = round(to * 100)
                    s = round(Sp)
                    S = round(Sp + Qp)

                    T_temp.append(T)
                    To_temp.append(To)
                    s_temp.append(s)
                    S_temp.append(S)
                
                for idx, temp in enumerate(T_temp):
                    if temp == min(T_temp):
                        index = idx
                        break

                return S_temp[index]
            
            def find_ss(x):
                # Hitung nilai To
                to = min_to

                # Hitung nilai alpha dan R
                alpha = to * biaya_simpan / biaya_kekurangan
                z_alpha = round((NormalDist().inv_cdf(alpha) * -1), 2)

                # fz_alpha = round(norm.pdf(2.22 , loc = 0 , scale = 1 ), 5)
                fz_alpha = round(norm.pdf(z_alpha , loc = 0 , scale = 1 ), 5)
                wz_alpha = fz_alpha - (z_alpha * (1 - fz_alpha))
                # wz_alpha = round((fz_alpha - 0.00001), 5)

                R = round((permintaan_baku * to) + (permintaan_baku * lead_time) + (z_alpha * (math.sqrt(to + lead_time))))

                # Hitung total biaya total persediaan
                N = math.ceil(standar_deviasi * ((math.sqrt(to + lead_time)) * ((fz_alpha - (z_alpha * wz_alpha)))))

                T = (permintaan_baku * harga_material) + (biaya_pesan / to) + (biaya_simpan * (R - (permintaan_baku * lead_time) + (permintaan_baku * to / 2))) + (biaya_kekurangan / to * N)

                # Hitung nilai XR, XRL, dan sigma_RL
                XR = to * permintaan_baku
                XRL = (to + lead_time) * permintaan_baku
                sigma_RL = (to + lead_time) * standar_deviasi

                Qp = round(1.3 * (XR ** 0.494) * ((biaya_pesan / (harga_material * biaya_simpan)) ** 0.506) * ((1 + ((sigma_RL ** 2) / (XR ** 2))) ** 0.116),2)
                z = math.sqrt((Qp * biaya_simpan) / (sigma_RL * biaya_kekurangan))
                if z <= 0:
                    Sp = round((0.973 * XRL) + (sigma_RL * ((0.183 / 1) + 1.063 - (2.192 * z))), 2)
                else:
                    Sp = round((0.973 * XRL) + (sigma_RL * ((0.183 / z) + 1.063 - (2.192 * z))), 2)

                k = round(biaya_simpan / (biaya_simpan + biaya_kekurangan), 2)

                So = round(XRL + (k * sigma_RL),2)

                s = round(Sp,2)
                S = round(Sp + Qp,2)

                temp = (permintaan_baku * harga_material) + (biaya_pesan / to)
                return temp, s, S
            
            initial=[0,0]               # initial starting location [x1,x2...]
            bounds=[(-10,10),(-10,10)]  # input bounds [(x1_min,x1_max),(x2_min,x2_max)...]
            min_to = PSO(func1,initial,bounds,num_particles=15,maxiter=30)
            s = PSO(func2,initial,bounds,num_particles=15,maxiter=30)
            S = PSO(func3,initial,bounds,num_particles=15,maxiter=30)

            biaya_inventory = find_ss(x)
            To = min_to * 100

            biaya_inventory = calculate_inventory_cost(x, min_to)

            temp = {
                'To': round(To),
                's': round(s),
                'S': round(S),
                'nama_barang': nama_barang,
                'biaya_inventory': round(biaya_inventory),

                # 'biaya_inventory_min': round(min(inventory_cost_list)),
                # 'biaya_inventory_mean': round(np.mean(inventory_cost_list)),
                # 'biaya_inventory_std': round(np.std(inventory_cost_list)),
            }

            data.append(temp)

        context = {
            'data': data,
        }

        return render(request, 'periodic/calculation.html', context)
    
    context = {
        'data': '',
    }

    return render(request, 'periodic/index.html', context)