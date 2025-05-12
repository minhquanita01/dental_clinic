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
    total_paid = serializers.SerializerMethodField(read_only=True)
    remaining_balance = serializers.SerializerMethodField(read_only=True)
    payment_status_percent = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = ('id', 'examination', 'examination_detail', 'patient', 'patient_detail', 
                  'staff', 'staff_detail', 'invoice_date', 'invoice_number', 'status', 
                  'status_display', 'subtotal', 'medicine_total', 'discount', 'tax', 
                  'total', 'total_paid', 'remaining_balance', 'payment_status_percent',
                  'notes', 'created_at', 'updated_at')
        read_only_fields = ('id', 'invoice_date', 'subtotal', 'medicine_total', 
                           'total', 'created_at', 'updated_at')
    
    def get_total_paid(self, obj):
        """Calculate total amount paid for this invoice."""
        return sum(payment.amount for payment in obj.payments.all())
    
    def get_remaining_balance(self, obj):
        """Calculate remaining balance to be paid."""
        total_paid = self.get_total_paid(obj)
        return max(0, obj.total - total_paid)
    
    def get_payment_status_percent(self, obj):
        """Calculate payment completion as percentage."""
        if obj.total <= 0:
            return 100
        total_paid = self.get_total_paid(obj)
        return min(100, int((total_paid / obj.total) * 100))
    
    def create(self, validated_data):
        """Create new invoice with auto-generated invoice number."""
        # Generate a unique invoice number
        last_invoice = Invoice.objects.order_by('-id').first()
        invoice_number = f"INV-{(last_invoice.id + 1 if last_invoice else 1):06d}"
        validated_data['invoice_number'] = invoice_number
        
        instance = super().create(validated_data)
        # Calculate totals
        instance.calculate_totals()
        return instance


class InvoiceListSerializer(InvoiceSerializer):
    """Simplified serializer for listing invoices."""
    
    class Meta(InvoiceSerializer.Meta):
        fields = ('id', 'invoice_number', 'patient_detail', 'invoice_date', 
                  'status', 'status_display', 'total', 'total_paid', 
                  'remaining_balance', 'payment_status_percent')


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    invoice_detail = InvoiceSerializer(source='invoice', read_only=True)
    staff_detail = UserPublicSerializer(source='staff', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_number = serializers.CharField(read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'invoice', 'invoice_detail', 'staff', 'staff_detail', 
                  'payment_date', 'payment_number', 'payment_method', 'payment_method_display',
                  'amount', 'reference_number', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('id', 'payment_date', 'payment_number', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create payment with auto-generated payment number."""
        # Generate a unique payment number
        last_payment = Payment.objects.order_by('-id').first()
        payment_number = f"PAY-{(last_payment.id + 1 if last_payment else 1):06d}"
        validated_data['payment_number'] = payment_number
        
        return super().create(validated_data)
    
    def validate(self, data):
        """Validate payment data."""
        # Check if invoice exists and is not already paid
        invoice = data.get('invoice')
        if invoice and invoice.status == Invoice.InvoiceStatus.PAID:
            raise serializers.ValidationError("This invoice is already fully paid.")
        
        # Check if amount is valid
        amount = data.get('amount', 0)
        if amount <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        
        # Check if amount doesn't exceed remaining balance
        total_paid = sum(payment.amount for payment in invoice.payments.all())
        remaining = invoice.total - total_paid
        if amount > remaining:
            raise serializers.ValidationError(f"Payment amount exceeds the remaining balance of {remaining}.")
        
        return data


class PaymentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing payments."""
    
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    patient_name = serializers.CharField(source='invoice.patient.full_name', read_only=True)
    staff_name = serializers.CharField(source='staff.full_name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = ('id', 'payment_number', 'invoice_number', 'patient_name', 
                  'staff_name', 'payment_date', 'amount', 'payment_method', 
                  'payment_method_display')