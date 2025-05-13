
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from medical_records.models import Examination
import datetime

# Create your models here.
class Invoice(models.Model):
    """Model sử dụng để lưu trữ thông tin hóa đơn."""
    
    class InvoiceStatus(models.TextChoices):
        PENDING = 'PENDING', _('Chờ thanh toán')
        PAID = 'PAID', _('Đã thanh toán')
        CANCELLED = 'CANCELLED', _('Đã hủy')
    
    examination = models.OneToOneField(
        Examination,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices',
        limit_choices_to={'user_type': User.UserType.CUSTOMER}
    )
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_invoices',
        limit_choices_to={'user_type__in': [User.UserType.STAFF, User.UserType.ADMIN]}
    )
    invoice_date = models.DateField(_('Ngày hóa đơn'), auto_now_add=True)
    invoice_number = models.CharField(_('Số hóa đơn'), max_length=50, unique=True)
    status = models.CharField(
        _('Trạng thái'),
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.PENDING
    )
    subtotal = models.DecimalField(_('Tổng tiền dịch vụ'), max_digits=12, decimal_places=0, default=0)
    medicine_total = models.DecimalField(_('Tổng tiền thuốc'), max_digits=12, decimal_places=0, default=0)
    discount = models.DecimalField(_('Giảm giá'), max_digits=12, decimal_places=0, default=0)
    tax = models.DecimalField(_('Thuế'), max_digits=12, decimal_places=0, default=0)
    total = models.DecimalField(_('Tổng cộng'), max_digits=12, decimal_places=0, default=0)
    notes = models.TextField(_('Ghi chú'), blank=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Cập nhật lần cuối'), auto_now=True)
    
    class Meta:
        verbose_name = _('Hóa đơn')
        verbose_name_plural = _('Hóa đơn')
        ordering = ['-invoice_date', '-created_at']
    
    def __str__(self):
        return f"Hóa đơn: {self.invoice_number} - {self.patient.full_name}"
    
    def calculate_totals(self):
        """Tính toán tổng tiền hóa đơn."""
        from medical_records.models import ExaminationService
        from pharmacy.models import PrescriptionItem
        
        # Calculate services total
        services = ExaminationService.objects.filter(examination=self.examination)
        self.subtotal = sum(service.price * service.quantity for service in services)
        
        # Calculate medicine total if prescription exists
        try:
            prescription = self.examination.prescription
            prescription_items = PrescriptionItem.objects.filter(prescription=prescription)
            self.medicine_total = sum(item.price * item.quantity for item in prescription_items)
        except:
            self.medicine_total = 0
        
        # Calculate total
        self.total = self.subtotal + self.medicine_total - self.discount + self.tax
        
        self.save()
    
    def generate_invoice_number(self):
        """Khởi tạo số hoá đơn duy nhất"""
        today = datetime.date.today()
        year = today.year
        month = today.month
        day = today.day
        
        # Lấy số hóa đơn đã tạo trong ngày hôm nay
        today_start = datetime.datetime.combine(today, datetime.time.min)
        count = Invoice.objects.filter(created_at__gte=today_start).count() + 1
        
        # Trả về số hóa đơn theo định dạng INV-YYYYMMDD-XXX với XXX là số thứ tự trong ngày, ví dụ: INV-20231001-001
        return f"INV-{year}{month:02d}{day:02d}-{count:03d}"
    
    def save(self, *args, **kwargs):
        # Khởi tạo số hóa đơn nếu chưa có
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Model sử dụng để lưu trữ thông tin thanh toán."""
    
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', _('Tiền mặt')
        CARD = 'CARD', _('Thẻ ngân hàng')
        TRANSFER = 'TRANSFER', _('Chuyển khoản')
        OTHER = 'OTHER', _('Khác')
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_date = models.DateTimeField(_('Ngày thanh toán'), auto_now_add=True)
    amount = models.DecimalField(_('Số tiền'), max_digits=12, decimal_places=0)
    payment_method = models.CharField(
        _('Phương thức thanh toán'),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    reference_number = models.CharField(_('Số tham chiếu'), max_length=100, blank=True)
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='processed_payments',
        limit_choices_to={'user_type__in': [User.UserType.STAFF, User.UserType.ADMIN]}
    )
    notes = models.TextField(_('Ghi chú'), blank=True)
    
    class Meta:
        verbose_name = _('Thanh toán')
        verbose_name_plural = _('Thanh toán')
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Thanh toán: {self.invoice.invoice_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Check if invoice is fully paid
        total_payments = sum(payment.amount for payment in self.invoice.payments.all())
        if total_payments >= self.invoice.total:
            self.invoice.status = Invoice.InvoiceStatus.PAID
            self.invoice.save()