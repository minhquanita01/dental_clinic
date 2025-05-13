from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy

# Create your models here.
class UserManager(BaseUserManager):
    """Define a model manager for User model."""

    def _create_user(self, phone_number, password=None, **extra_fields):
        """Create and save a User with the given phone number and password."""
        if not phone_number:
            raise ValueError('The phone number must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        """Create and save a regular User with the given phone number and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Create and save a SuperUser with the given phone number and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', User.UserType.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    """Custom User model for dental clinic system."""
    
    class UserType(models.TextChoices):
        CUSTOMER = 'CUSTOMER', gettext_lazy('Khách hàng')
        DENTIST = 'DENTIST', gettext_lazy('Nha sĩ')
        STAFF = 'STAFF', gettext_lazy('Nhân viên')
        ADMIN = 'ADMIN', gettext_lazy('Quản trị viên')
    
    username = None
    phone_number = models.CharField(gettext_lazy('Số điện thoại'), max_length=15, unique=True)
    full_name = models.CharField(gettext_lazy('Họ tên'), max_length=255)
    date_of_birth = models.DateField(gettext_lazy('Ngày sinh'), null=True, blank=True)
    address = models.TextField(gettext_lazy('Địa chỉ'), blank=True)
    user_type = models.CharField(gettext_lazy('Loại người dùng'), max_length=10, choices=UserType.choices, default=UserType.CUSTOMER)
    is_active = models.BooleanField(gettext_lazy('Đang hoạt động'), default=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = gettext_lazy('Người dùng')
        verbose_name_plural = gettext_lazy('Người dùng')

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class DentistProfile(models.Model):
    """Profile for dentists with additional information."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='dentist_profile',
        limit_choices_to={'user_type': User.UserType.DENTIST},
        primary_key=True,
        verbose_name = "Nha sĩ"
    )
    specialization = models.CharField(gettext_lazy('Chuyên môn'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = gettext_lazy('Hồ sơ nha sĩ')
        verbose_name_plural = gettext_lazy('Hồ sơ nha sĩ')
    
    def __str__(self):
        return f"Nha sĩ: {self.user.full_name}"