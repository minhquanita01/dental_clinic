import django_filters
from django.forms import DateInput
from .models import Invoice, Payment

class InvoiceFilter(django_filters.FilterSet):
    """Bộ lọc nâng cao cho hóa đơn"""
    invoice_date_min = django_filters.DateFilter(
        field_name='invoice_date',
        lookup_expr='gte',
        widget=DateInput(attrs={'type': 'date'})
    )
    invoice_date_max = django_filters.DateFilter(
        field_name='invoice_date',
        lookup_expr='lte',
        widget=DateInput(attrs={'type': 'date'})
    )
    total_min = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    total_max = django_filters.NumberFilter(field_name='total', lookup_expr='lte')
    
    class Meta:
        model = Invoice
        fields = {
            'invoice_number': ['exact', 'contains'],
            'patient__full_name': ['contains'],
            'status': ['exact'],
            'examination__examination_date': ['exact', 'year', 'month'],
        }

class PaymentFilter(django_filters.FilterSet):
    """Bộ lọc nâng cao cho thanh toán"""
    payment_date_min = django_filters.DateFilter(
        field_name='payment_date',
        lookup_expr='gte',
        widget=DateInput(attrs={'type': 'date'})
    )
    payment_date_max = django_filters.DateFilter(
        field_name='payment_date',
        lookup_expr='lte',
        widget=DateInput(attrs={'type': 'date'})
    )
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    class Meta:
        model = Payment
        fields = {
            'payment_method': ['exact'],
            'invoice__invoice_number': ['exact', 'contains'],
            'invoice__patient__full_name': ['contains'],
        }