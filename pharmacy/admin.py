from django.contrib import admin
from .models import Medicine, Prescription, PrescriptionItem, MedicineStock


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    """Admin configuration for Medicine model."""
    
    list_display = (
        'name', 
        'code', 
        'unit', 
        'quantity_in_stock', 
        'expiry_date', 
        'price', 
        'is_active'
    )
    list_filter = ('is_active', 'expiry_date')
    search_fields = ('name', 'code')
    list_per_page = 20


class PrescriptionItemInline(admin.TabularInline):
    """Inline admin for PrescriptionItem."""
    
    model = PrescriptionItem
    extra = 1
    readonly_fields = ('price',)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Admin configuration for Prescription model."""
    
    list_display = (
        'id', 
        'examination', 
        'prescription_date'
    )
    list_filter = ('prescription_date',)
    inlines = [PrescriptionItemInline]
    readonly_fields = ('prescription_date',)
    search_fields = ('examination__medical_record__patient__full_name',)
    list_per_page = 20


@admin.register(MedicineStock)
class MedicineStockAdmin(admin.ModelAdmin):
    """Admin configuration for MedicineStock model."""
    
    list_display = (
        'medicine', 
        'quantity', 
        'stock_type', 
        'created_at', 
        'reference'
    )
    list_filter = ('stock_type', 'created_at')
    search_fields = ('medicine__name', 'reference')
    list_per_page = 20