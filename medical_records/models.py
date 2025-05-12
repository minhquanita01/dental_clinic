
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from appointments.models import Appointment

# Create your models here.
class DentalService(models.Model):
    """Model for storing dental services information."""
    
    name = models.CharField(_('Tên dịch vụ'), max_length=255)
    description = models.TextField(_('Mô tả dịch vụ'), blank=True)
    price = models.DecimalField(_('Giá'), max_digits=10, decimal_places=0)
    
    class Meta:
        verbose_name = _('Dịch vụ nha khoa')
        verbose_name_plural = _('Dịch vụ nha khoa')
    
    def __str__(self):
        return self.name


class MedicalRecord(models.Model):
    """Main medical record for a patient."""
    
    patient = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='medical_record',
        limit_choices_to={'user_type': User.UserType.CUSTOMER}
    )
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Cập nhật lần cuối'), auto_now=True)
    notes = models.TextField(_('Ghi chú chung'), blank=True)
    
    class Meta:
        verbose_name = _('Hồ sơ bệnh án')
        verbose_name_plural = _('Hồ sơ bệnh án')
    
    def __str__(self):
        return f"Hồ sơ bệnh án: {self.patient.full_name}"


class Examination(models.Model):
    """Model for storing examination information."""
    
    medical_record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='examinations'
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='examination'
    )
    dentist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='performed_examinations',
        limit_choices_to={'user_type': User.UserType.DENTIST}
    )
    examination_date = models.DateField(_('Ngày khám'))
    diagnosis = models.TextField(_('Chẩn đoán'))
    treatment_plan = models.TextField(_('Kế hoạch điều trị'), blank=True)
    notes = models.TextField(_('Ghi chú'), blank=True)
    
    class Meta:
        verbose_name = _('Lần khám')
        verbose_name_plural = _('Lần khám')
        ordering = ['-examination_date']
    
    def __str__(self):
        return f"{self.medical_record.patient.full_name} - {self.examination_date}"


class ExaminationService(models.Model):
    """Services used in an examination."""
    
    examination = models.ForeignKey(
        Examination,
        on_delete=models.CASCADE,
        related_name='services'
    )
    service = models.ForeignKey(
        DentalService,
        on_delete=models.CASCADE,
        related_name='examination_services'
    )
    quantity = models.PositiveIntegerField(_('Số lượng'), default=1)
    price = models.DecimalField(_('Giá áp dụng'), max_digits=10, decimal_places=0)
    notes = models.TextField(_('Ghi chú'), blank=True)
    
    class Meta:
        verbose_name = _('Dịch vụ đã sử dụng')
        verbose_name_plural = _('Dịch vụ đã sử dụng')
    
    def __str__(self):
        return f"{self.examination} - {self.service.name}"
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.service.price
        super().save(*args, **kwargs)