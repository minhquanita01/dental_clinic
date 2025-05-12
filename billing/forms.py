from django import forms
from .models import Invoice, Payment

class InvoiceForm(forms.ModelForm):
    """Form cho hóa đơn"""
    class Meta:
        model = Invoice
        fields = ['examination', 'patient', 'discount', 'tax', 'notes', 'status']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PaymentForm(forms.ModelForm):
    """Form cho thanh toán"""
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }