from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from medical_records.models import Examination
from .models import Invoice

@receiver(post_save, sender=Examination)
def create_invoice_for_examination(sender, instance, created, **kwargs):
    """
    Tự động tạo hóa đơn sau khi tạo một lần khám mới.
    """
    if created:
        # Tạo một hóa đơn mới nếu chưa có
        if not hasattr(instance, 'invoice'):
            # Generate a unique invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            invoice_number = f"INV-{(last_invoice.id + 1 if last_invoice else 1):06d}"
            
            # Tạo hóa đơn mới
            invoice = Invoice.objects.create(
                examination=instance,
                patient=instance.medical_record.patient,
                staff=instance.dentist,  # Nha sĩ thực hiện khám sẽ là người tạo hóa đơn tạm thời
                invoice_number=invoice_number,
                status=Invoice.InvoiceStatus.PENDING
            )
            
            # Tính tổng hóa đơn dựa trên dịch vụ đã sử dụng
            invoice.calculate_totals()