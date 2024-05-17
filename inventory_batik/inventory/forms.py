from django.forms import ModelForm
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

class ItemForm(ModelForm):
    class Meta:
        # merelasikan form dengan model
        model = Item
        # mengeset field apa saja yang akan ditampilkan pada form
        fields = ('code', 'name', 'image', 'description', 'price', 'type', 'biaya_pesan', 'lead_time')
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

class MaterialForm(ModelForm):
    class Meta:
        # merelasikan form dengan model
        model = Material
        # mengeset field apa saja yang akan ditampilkan pada form
        fields = ('code', 'name', 'image', 'description', 'price', 'unit', 'biaya_pesan', 'lead_time')
        # mengatur teks label untuk setiap field
        labels = {
            'code': _('Kode Item'),
            'name': _('Nama Item'),
            'description': _('Deskripsi Item'),
            'price': _('Harga Item'),
            'unit': _('Unit Item'),
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

class PurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        fields = ('outlet', 'item', 'price', 'amount', 'unit')
        labels = {
            'outlet': _('Pilih Outlet'),
            'Item': _('Pilih Barang'),
            'price': _('Harga Beli'),
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

class ProductionForm(ModelForm):
    class Meta:
        model = Production
        fields = ('outlet', 'item', 'amount')
        labels = {
            'outlet': _('Pilih Outlet'),
            'Item': _('Pilih Barang'),
            'amount': _('Jumlah Pembelian'),
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

class SalesForm(ModelForm):
    class Meta:
        model = Sales
        fields = ('outlet', 'item', 'price', 'amount', 'unit')
        labels = {
            'outlet': _('Pilih Outlet'),
            'Item': _('Pilih Barang'),
            'price': _('Harga Jual'),
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
                'required': _("Deskripsi item harus diisi."),
            },
            'price': {
                'required': _("Harga item harus diisi."),
            },
            'type': {
                'required': _("Tipe item harus diisi."),
            },
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
