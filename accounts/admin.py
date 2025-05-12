from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, DentistProfile


class DentistProfileInline(admin.StackedInline):
    model = DentistProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ nha sĩ'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        (_('Thông tin cá nhân'), {'fields': ('full_name', 'date_of_birth', 'address')}),
        (_('Phân quyền'), {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser')}),
        (_('Ngày quan trọng'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'full_name', 'user_type'),
        }),
    )
    list_display = ('phone_number', 'full_name', 'user_type', 'is_active')
    list_filter = ('is_active', 'user_type')
    search_fields = ('phone_number', 'full_name')
    ordering = ('phone_number',)
    
    def get_inlines(self, request, obj=None):
        if obj and obj.user_type == User.UserType.DENTIST:
            return [DentistProfileInline]
        return []


@admin.register(DentistProfile)
class DentistProfileAdmin(admin.ModelAdmin):
    """Admin configuration for DentistProfile model."""
    
    list_display = ('user', 'specialization')
    search_fields = ('user__full_name', 'user__phone_number', 'specialization')