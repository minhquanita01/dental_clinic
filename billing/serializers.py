from rest_framework import serializers
from .models import Invoice, Payment
from accounts.serializers import UserPublicSerializer
from medical_records.serializers import ExaminationSerializer


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    
    patient_detail = UserPublicSerializer(source='patient', read_only=True)
    staff_detail = UserPublicSerializer(source='staff', read_only=True)
    examination_detail = ExaminationSerializer(source='examination', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Invoice
        fields = ('id', 'examination', 'examination_detail', 'patient', 'patient_detail', 
                  'staff', 'staff_detail', 'invoice_date', 'invoice_number', 'status', 
                  'status_display', 'subtotal', 'medicine_total', 'discount', 'tax', 
                  'total', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('id', 'invoice_date', 'subtotal', 'medicine_total', 
                           'total', 'created_at', 'updated_at')


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    invoice_detail = InvoiceSerializer(source='invoice', read_only=True)
    staff_detail = UserPublicSerializer(source='staff', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)