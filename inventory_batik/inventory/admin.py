from django.contrib import admin

# Register your models here.
from .models import Responden, Jawaban

class JawabanInline(admin.TabularInline):
    model = Jawaban
    extra = 0

@admin.register(Responden)
class RespondenAdmin(admin.ModelAdmin):
    list_display  = ('nama', 'umkm', 'usia', 'pendidikan_terakhir', 'submitted_at')
    search_fields = ('nama', 'umkm')
    inlines       = [JawabanInline]

@admin.register(Jawaban)
class JawabanAdmin(admin.ModelAdmin):
    list_display  = ('responden', 'variabel', 'kode_item', 'skor')
    list_filter   = ('variabel',)