from django.db import models
from .utils import *

class Outlet(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'outlets'

    def __str__(self):
        return '%s' % self.name

class Item(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="img/items/", null=True, blank=True)
    description = models.TextField()
    user_id = models.IntegerField()
    price = models.IntegerField()
    biaya_pesan = models.IntegerField(default=None, null=True)
    lead_time = models.IntegerField(default=None, null=True)
    type = models.CharField(max_length=255, choices=ItemTypes.choices(), default=ItemTypes.MENTAH)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'items'

    def __str__(self):
        return '%s' % self.name
    
class Material(models.Model):
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    user_id = models.IntegerField()
    image = models.ImageField(upload_to="img/items/", null=True, blank=True)
    description = models.TextField()
    price = models.IntegerField()
    biaya_pesan = models.IntegerField(default=None, null=True)
    lead_time = models.IntegerField(default=None, null=True)
    unit = models.CharField(max_length=255, choices=UnitTypes.choices(), default=UnitTypes.KG)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'materials'

    def __str__(self):
        return '%s' % self.name

class Purchase(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    price = models.CharField(max_length=255)
    amount = models.IntegerField()
    unit = models.CharField(max_length=255, choices=UnitTypes.choices(), default=UnitTypes.KG)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'purchases'

class Sales(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price = models.CharField(max_length=255)
    amount = models.IntegerField()
    user_id = models.IntegerField()
    unit = models.CharField(max_length=255, choices=UnitTypes.choices(), default=UnitTypes.KG)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sales'

class Production(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.IntegerField()
    user_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'productions'

class Stock(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stocks'

class Transaction(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, null=True)
    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, null=True)
    type = models.CharField(max_length=255, choices=TypeTypes.choices(), default=TypeTypes.PURCHASE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'

class Recipe(models.Model):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    amount = models.IntegerField()
    unit = models.CharField(max_length=255, choices=UnitTypes.choices(), default=UnitTypes.KG)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipes'

class Responden(models.Model):
    USIA_CHOICES = [
        ('< 20', '< 20 tahun'),
        ('20-30', '20–30 tahun'),
        ('31-40', '31–40 tahun'),
        ('41-50', '41–50 tahun'),
        ('> 50', '> 50 tahun'),
    ]

    PENDIDIKAN_CHOICES = [
        ('SD', 'SD'),
        ('SMP', 'SMP'),
        ('SMA', 'SMA/SMK'),
        ('D3', 'D3'),
        ('S1', 'S1'),
        ('S2', 'S2'),
        ('S3', 'S3'),
    ]

    nama              = models.CharField(max_length=150)
    usia              = models.CharField(max_length=10, choices=USIA_CHOICES)
    pendidikan_terakhir = models.CharField(max_length=5, choices=PENDIDIKAN_CHOICES)
    umkm              = models.CharField(max_length=200)
    address           = models.TextField()
    phone_number      = models.CharField(max_length=20)
    submitted_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nama} — {self.umkm}"

    class Meta:
        db_table = 'responden'
        verbose_name_plural = 'Responden'


class Jawaban(models.Model):
    VARIABEL_CHOICES = [
        ('PEOU', 'Perceived Easy of Use'),
        ('PU',   'Perceived Usefulness'),
        ('CONF', 'Confirmation'),
        ('ATT',  'Attitude'),
        ('TRST', 'Trust'),
        ('SAT',  'Satisfaction'),
        ('CI',   'Continuance Intention'),
    ]

    SKOR_CHOICES = [
        (1, 'STS – Sangat Tidak Setuju'),
        (2, 'TS – Tidak Setuju'),
        (3, 'S – Setuju'),
        (4, 'SS – Sangat Setuju'),
    ]

    responden  = models.ForeignKey(
        Responden,
        on_delete=models.CASCADE,
        related_name='jawaban'
    )
    variabel   = models.CharField(max_length=5, choices=VARIABEL_CHOICES)
    kode_item  = models.CharField(max_length=10)  # e.g. "PEOU_1", "PU_3"
    skor       = models.PositiveSmallIntegerField(choices=SKOR_CHOICES)

    def __str__(self):
        return f"{self.responden.nama} | {self.kode_item} = {self.skor}"

    class Meta:
        db_table = 'jawaban'
        unique_together = ('responden', 'kode_item')