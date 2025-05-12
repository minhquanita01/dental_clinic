
from django.db import models
from django.utils.translation import gettext_lazy as _
from medical_records.models import Examination

# Create your models here.
class Medicine(models.Model):
    """Model for storing medicine information."""
    
    code = models.CharField(_('Mã thuốc'), max_length=50, unique=True)
    name = models.CharField(_('Tên thuốc'), max_length=255)
    unit = models.CharField(_('Đơn vị tính'), max_length=50)
    indication = models.TextField(_('Chỉ định'), blank=True)
    quantity_in_stock = models.PositiveIntegerField(_('Số lượng tồn kho'), default=0)
    expiry_date = models.DateField(_('Ngày hết hạn'))
    price = models.DecimalField(_('Giá'), max_digits=10, decimal_places=0)
    is_active = models.BooleanField(_('Còn sử dụng'), default=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Cập nhật lần cuối'), auto_now=True)
    
    class Meta:
        verbose_name = _('Thuốc')
        verbose_name_plural = _('Thuốc')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Prescription(models.Model):
    """Model for storing prescription information."""
    
    examination = models.OneToOneField(
        Examination,
        on_delete=models.CASCADE,
        related_name='prescription'
    )
    prescription_date = models.DateField(_('Ngày kê đơn'), auto_now_add=True)
    notes = models.TextField(_('Ghi chú'), blank=True)
    
    class Meta:
        verbose_name = _('Đơn thuốc')
        verbose_name_plural = _('Đơn thuốc')
        ordering = ['-prescription_date']
    
    def __str__(self):
        return f"Đơn thuốc: {self.examination.medical_record.patient.full_name} - {self.prescription_date}"


class PrescriptionItem(models.Model):
    """Items in a prescription."""
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items'
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='prescription_items'
    )
    quantity = models.PositiveIntegerField(_('Số lượng'))
    dosage = models.CharField(_('Liều dùng'), max_length=255)
    instructions = models.TextField(_('Hướng dẫn sử dụng'))
    price = models.DecimalField(_('Giá áp dụng'), max_digits=10, decimal_places=0)
    
    class Meta:
        verbose_name = _('Chi tiết đơn thuốc')
        verbose_name_plural = _('Chi tiết đơn thuốc')
    
    def __str__(self):
        return f"{self.medicine.name} - {self.quantity} {self.medicine.unit}"
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.medicine.price
        super().save(*args, **kwargs)


class MedicineStock(models.Model):
    """Model for tracking medicine stock movements."""
    
    class StockType(models.TextChoices):
        IMPORT = 'IMPORT', _('Nhập kho')
        EXPORT = 'EXPORT', _('Xuất kho')
        ADJUST = 'ADJUST', _('Điều chỉnh')
    
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='stock_records'
    )
    quantity = models.IntegerField(_('Số lượng'))  # Positive for import, negative for export
    stock_type = models.CharField(
        _('Loại'),
        max_length=10,
        choices=StockType.choices
    )
    reference = models.CharField(_('Mã tham chiếu'), max_length=255, blank=True)
    notes = models.TextField(_('Ghi chú'), blank=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Biến động kho thuốc')
        verbose_name_plural = _('Biến động kho thuốc')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medicine.name} - {self.stock_type} - {self.quantity}"