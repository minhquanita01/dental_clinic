from django.contrib import admin
from .models import Invoice, Payment

# Register your models here.
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_date',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'patient', 'invoice_date', 'total', 'status')
    list_filter = ('status', 'invoice_date')
    search_fields = ('invoice_number', 'patient__full_name', 'patient__phone_number')
    readonly_fields = ('invoice_date', 'subtotal', 'medicine_total', 'total')
    inlines = [PaymentInline]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('invoice_number', 'patient', 'staff', 'examination', 'invoice_date', 'status')
        }),
        ('Giá trị', {
            'fields': ('subtotal', 'medicine_total', 'discount', 'tax', 'total')
        }),
        ('Ghi chú', {
            'fields': ('notes',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nếu là tạo mới
            obj.staff = request.user
        super().save_model(request, obj, form, change)
        # Tính toán lại tổng
        obj.calculate_totals()

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('get_payment_number', 'invoice', 'payment_date', 'amount', 'payment_method', 'staff')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('reference_number', 'invoice__invoice_number', 'invoice__patient__full_name')
    readonly_fields = ('payment_date',)
    
    fieldsets = (
        ('Thông tin thanh toán', {
            'fields': ('invoice', 'amount', 'payment_method', 'reference_number', 'staff')
        }),
        ('Ghi chú', {
            'fields': ('notes',)
        }),
    )
    
    def get_payment_number(self, obj):
        return f"PAY-{obj.id:06d}" if obj.id else "Chưa lưu"
    get_payment_number.short_description = "Mã thanh toán"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nếu là tạo mới
            obj.staff = request.user
        super().save_model(request, obj, form, change)