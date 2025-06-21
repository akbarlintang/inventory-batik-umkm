from django.forms import ModelForm
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import *

class OutletForm(ModelForm):
    class Meta:
        # merelasikan form dengan model
        model = Outlet
        # mengeset field apa saja yang akan ditampilkan pada form
        fields = ('name', 'address')
        # mengatur teks label untuk setiap field
        labels = {
            'name': _('Nama Outlet'),
            'address': _('Alamat Outlet'),
        }
        # mengatur teks pesan error untuk setiap validasi fieldnya
        error_messages = {
            'name': {
                'required': _("Nama outlet harus diisi."),
            },
            'address': {
                'required': _("Alamat outlet harus diisi."),
            },
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Gudang A', 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'placeholder': 'Jl. Ahmad Yani No. 34', 'class': 'form-control'}),
        }

class ItemForm(ModelForm):
    class Meta:
        # merelasikan form dengan model
        model = Item
        # mengeset field apa saja yang akan ditampilkan pada form
        fields = ('code', 'name', 'description', 'price', 'type', 'biaya_pesan', 'lead_time')
        # mengatur teks label untuk setiap field
        labels = {
            'code': _('Kode Item'),
            'name': _('Nama Item'),
            'description': _('Deskripsi Item'),
            'price': _('Harga Item'),
            'type': _('Tipe Item'),
            'biaya_pesan': _('Biaya Pesan Item'),
            'lead_time': _('Lead Time Pemenuhan Item'),
        }
        # mengatur teks pesan error untuk setiap validasi fieldnya
        error_messages = {
            'code': {
                'required': _("Kode item harus diisi."),
            },
            'name': {
                'required': _("Nama item harus diisi."),
            },
            'description': {
                'required': _("Deksripsi item harus diisi."),
            },
            'price': {
                'required': _("Harga item harus diisi."),
            },
            'type': {
                'required': _("Tipe item harus diisi."),
            },
            'biaya_pesan': {
                'required': _("Biaya pesan item harus diisi."),
            },
            'lead_time': {
                'required': _("Lead Time pemenuhan item harus diisi."),
            },
        }
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'KTN-001', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'placeholder': 'Katun Grade A', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'placeholder': 'Kain katun dengan kualitas tingkat tinggi', 'class': 'form-control'}),
            'price': forms.TextInput(attrs={'placeholder': '100000', 'class': 'form-control'}),
            'biaya_pesan': forms.TextInput(attrs={'placeholder': '12000', 'class': 'form-control'}),
            'lead_time': forms.TextInput(attrs={'placeholder': '2', 'class': 'form-control'}),
        }

class MaterialForm(ModelForm):
    class Meta:
        # merelasikan form dengan model
        model = Material
        # mengeset field apa saja yang akan ditampilkan pada form
        fields = ('code', 'name', 'description', 'price', 'unit', 'biaya_pesan', 'lead_time')
        # mengatur teks label untuk setiap field
        labels = {
            'code': _('Kode Item'),
            'name': _('Nama Item'),
            'description': _('Deskripsi Item'),
            'price': _('Harga Item'),
            'unit': _('Unit Item'),
            'biaya_pesan': _('Biaya Pesan Item (transportasi, internet, dll.)'),
            'lead_time': _('Lead Time Pemenuhan Item (Druasi pemesanan)'),
        }
        # mengatur teks pesan error untuk setiap validasi fieldnya
        error_messages = {
            'code': {
                'required': _("Kode item harus diisi."),
            },
            'name': {
                'required': _("Nama item harus diisi."),
            },
            'description': {
                'required': _("Deksripsi item harus diisi."),
            },
            'price': {
                'required': _("Harga item harus diisi."),
            },
            'unit': {
                'required': _("Tipe item harus diisi."),
            },
            'biaya_pesan': {
                'required': _("Biaya pesan item harus diisi."),
            },
            'lead_time': {
                'required': _("Lead Time pemenuhan item harus diisi."),
            },
        }
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'P001', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'placeholder': 'Pewarna Merah A', 'class': 'form-control'}),
            'description': forms.TextInput(attrs={'placeholder': 'Pewarna  merah 1 liter', 'class': 'form-control'}),
            'price': forms.TextInput(attrs={'placeholder': '50000', 'class': 'form-control'}),
            'biaya_pesan': forms.TextInput(attrs={'placeholder': '4000', 'class': 'form-control'}),
            'lead_time': forms.TextInput(attrs={'placeholder': '2', 'class': 'form-control'}),
        }

class PurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        fields = ('outlet', 'item', 'price', 'amount', 'unit')
        labels = {
            'outlet': _('Pilih Outlet'),
            'item': _('Pilih Barang'),
            'price': _('Total Harga Pembelian'),
            'amount': _('Jumlah Pembelian'),
            'unit': _('Satuan Barang'),
        }
        error_messages = {
            'code': {
                'required': _("Kode item harus diisi."),
            },
            'name': {
                'required': _("Nama item harus diisi."),
            },
            'description': {
                'required': _("Deksripsi item harus diisi."),
            },
            'price': {
                'required': _("Harga item harus diisi."),
            },
            'type': {
                'required': _("Tipe item harus diisi."),
            },
        }
        widgets = {
            'price': forms.TextInput(attrs={'placeholder': '50000', 'class': 'form-control'}),
            'amount': forms.TextInput(attrs={'placeholder': '10', 'class': 'form-control'}),
        }

class ProductionForm(ModelForm):
    class Meta:
        model = Production
        fields = ('outlet', 'item', 'amount')
        labels = {
            'outlet': _('Pilih Outlet'),
            'item': _('Pilih Barang'),
            'amount': _('Jumlah Produksi'),
        }
        error_messages = {
            'outlet': {
                'required': _("Outlet harus diisi."),
            },
            'item': {
                'required': _("Item harus diisi."),
            },
            'amount': {
                'required': _("Jumlah item harus diisi."),
            },
        }
        widgets = {
            'amount': forms.TextInput(attrs={'placeholder': '100', 'class': 'form-control'}),
        }

class SalesForm(ModelForm):
    class Meta:
        model = Sales
        fields = ('outlet', 'item', 'price', 'amount', 'unit')
        labels = {
            'outlet': _('Pilih Outlet'),
            'item': _('Pilih Barang'),
            'price': _('Harga Jual'),
            'amount': _('Jumlah'),
            'unit': _('Satuan Barang'),
        }
        error_messages = {
            'code': {
                'required': _("Kode item harus diisi."),
            },
            'name': {
                'required': _("Nama item harus diisi."),
            },
            'description': {
                'required': _("Deskripsi item harus diisi."),
            },
            'price': {
                'required': _("Harga item harus diisi."),
            },
            'type': {
                'required': _("Tipe item harus diisi."),
            },
        }
        widgets = {
            'price': forms.TextInput(attrs={'placeholder': '120000', 'class': 'form-control'}),
            'amount': forms.TextInput(attrs={'placeholder': '300', 'class': 'form-control'}),
        }

class TransactionForm(ModelForm):
    class Meta:
        model = Transaction
        fields = "__all__"

class RecipeForm(ModelForm):
    class Meta:
        model = Recipe
        exclude = ['item']
        fields = ('outlet', 'material', 'amount')
        labels = {
            'outlet': _('Pilih Outlet'),
            'material': _('Pilih Material'),
            'amount': _('Jumlah Material'),
        }
        error_messages = {
            'outlet': {
                'required': _("Outlet harus diisi."),
            },
            'material': {
                'required': _("Material harus diisi."),
            },
            'amount': {
                'required': _("Jumlah item harus diisi."),
            },
        }
        widgets = {
            'amount': forms.TextInput(attrs={'placeholder': '10', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Pop 'user' from kwargs to use it in filtering
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            # Example: Filter outlet and material based on user
            self.fields['outlet'].queryset = Outlet.objects.filter(user_id=user)
            self.fields['material'].queryset = Material.objects.filter(user_id=user)
