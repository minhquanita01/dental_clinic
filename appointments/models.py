
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User

# Create your models here.
class Appointment(models.Model):
    """Model for storing appointment information."""
    
    class AppointmentStatus(models.TextChoices):
        PENDING = 'PENDING', _('Chờ xác nhận')
        CONFIRMED = 'CONFIRMED', _('Đã xác nhận')
        COMPLETED = 'COMPLETED', _('Đã hoàn thành')
        CANCELLED = 'CANCELLED', _('Đã hủy')
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='patient_appointments',
        limit_choices_to={'user_type': User.UserType.CUSTOMER}
    )
    dentist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dentist_appointments',
        limit_choices_to={'user_type': User.UserType.DENTIST}
    )
    appointment_date = models.DateField(_('Ngày hẹn'))
    appointment_time = models.TimeField(_('Giờ hẹn'))
    reason = models.TextField(_('Lý do khám'), blank=True)
    status = models.CharField(
        _('Trạng thái'),
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING
    )
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Cập nhật lần cuối'), auto_now=True)
    
    class Meta:
        verbose_name = _('Lịch hẹn')
        verbose_name_plural = _('Lịch hẹn')
        ordering = ['-appointment_date', '-appointment_time']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.appointment_date} {self.appointment_time}"


class DentistSchedule(models.Model):
    """Model for storing dentist's working schedule."""
    
    WEEKDAY_CHOICES = [
        (0, _('Thứ hai')),
        (1, _('Thứ ba')),
        (2, _('Thứ tư')),
        (3, _('Thứ năm')),
        (4, _('Thứ sáu')),
        (5, _('Thứ bảy')),
        (6, _('Chủ nhật')),
    ]
    
    dentist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'user_type': User.UserType.DENTIST}
    )
    weekday = models.IntegerField(_('Ngày trong tuần'), choices=WEEKDAY_CHOICES)
    start_time = models.TimeField(_('Giờ bắt đầu'))
    end_time = models.TimeField(_('Giờ kết thúc'))
    is_available = models.BooleanField(_('Khả dụng'), default=True)
    
    class Meta:
        verbose_name = _('Lịch làm việc')
        verbose_name_plural = _('Lịch làm việc')
        unique_together = ('dentist', 'weekday', 'start_time', 'end_time')
        ordering = ['weekday', 'start_time']
    
    def __str__(self):
        return f"{self.dentist.full_name} - {self.get_weekday_display()} ({self.start_time}-{self.end_time})"


class DentistTimeOff(models.Model):
    """Model for storing dentist's time off."""
    
    dentist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_offs',
        limit_choices_to={'user_type': User.UserType.DENTIST}
    )
    start_date = models.DateField(_('Ngày bắt đầu'))
    end_date = models.DateField(_('Ngày kết thúc'))
    reason = models.TextField(_('Lý do'), blank=True)
    
    class Meta:
        verbose_name = _('Ngày nghỉ')
        verbose_name_plural = _('Ngày nghỉ')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.dentist.full_name} - {self.start_date} đến {self.end_date}"
    