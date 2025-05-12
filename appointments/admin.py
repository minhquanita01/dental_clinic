from django.contrib import admin
from .models import Appointment, DentistSchedule, DentistTimeOff


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin configuration for Appointments."""
    
    list_display = ('patient', 'dentist', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date', 'dentist')
    search_fields = ('patient__full_name', 'dentist__full_name')
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only for non-admin users."""
        if not request.user.is_superuser:
            return ['patient', 'dentist', 'created_at', 'updated_at']
        return []


@admin.register(DentistSchedule)
class DentistScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for Dentist Schedules."""
    
    list_display = ('dentist', 'weekday', 'start_time', 'end_time', 'is_available')
    list_filter = ('dentist', 'weekday', 'is_available')
    search_fields = ('dentist__full_name',)


@admin.register(DentistTimeOff)
class DentistTimeOffAdmin(admin.ModelAdmin):
    """Admin configuration for Dentist Time Off."""
    
    list_display = ('dentist', 'start_date', 'end_date', 'reason')
    list_filter = ('dentist', 'start_date', 'end_date')
    search_fields = ('dentist__full_name', 'reason')