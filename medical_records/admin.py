from django.contrib import admin
from .models import (
    DentalService, 
    MedicalRecord, 
    Examination, 
    ExaminationService
)

@admin.register(DentalService)
class DentalServiceAdmin(admin.ModelAdmin):
    """Admin configuration for Dental Services."""
    list_display = ('name', 'price', 'description')
    search_fields = ('name', 'description')
    list_filter = ('price',)


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """Admin configuration for Medical Records."""
    list_display = ('patient', 'created_at', 'updated_at')
    search_fields = ('patient__full_name', 'patient__phone_number')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    """Admin configuration for Examinations."""
    list_display = ('medical_record', 'dentist', 'examination_date', 'diagnosis')
    search_fields = (
        'medical_record__patient__full_name', 
        'dentist__full_name', 
        'diagnosis'
    )
    list_filter = ('examination_date', 'dentist')
    autocomplete_fields = ['medical_record', 'dentist', 'appointment']


@admin.register(ExaminationService)
class ExaminationServiceAdmin(admin.ModelAdmin):
    """Admin configuration for Examination Services."""
    list_display = ('examination', 'service', 'quantity', 'price')
    search_fields = (
        'examination__medical_record__patient__full_name', 
        'service__name'
    )
    list_filter = ('service',)
    autocomplete_fields = ['examination', 'service']