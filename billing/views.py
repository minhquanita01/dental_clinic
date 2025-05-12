from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .models import Invoice, Payment
from .serializers import (
    InvoiceSerializer, InvoiceListSerializer,
    PaymentSerializer, PaymentListSerializer
)
from accounts.permissions import IsStaffOrAdmin
from .filters import InvoiceFilter, PaymentFilter

# Các module cần thiết cho việc xuất báo cáo hóa đơn và thanh toán
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import csv
from django.http import HttpResponse

# Các module cần thiết cho việc hiển thị trang in hoá đơn
from django.shortcuts import render, get_object_or_404
from django.views import View
from medical_records.models import ExaminationService
from pharmacy.models import PrescriptionItem


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoices.
    """
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InvoiceFilter
    filterset_fields = ['status', 'patient', 'invoice_date', 'examination']
    search_fields = ['invoice_number', 'patient__full_name', 'notes']
    ordering_fields = ['invoice_date', 'total', 'created_at', 'updated_at']
    ordering = ['-invoice_date']

    def get_serializer_class(self):
        """Return different serializers based on action."""
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer

    def get_permissions(self):
        """
        Only admin and staff can manage invoices.
        """
        permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set the staff to the current user when creating an invoice."""
        serializer.save(staff=self.request.user)
    
    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        """Recalculate invoice totals."""
        invoice = self.get_object()
        invoice.calculate_totals()
        return Response(
            InvoiceSerializer(invoice).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False)
    def pending(self, request):
        """Get pending invoices."""
        invoices = self.queryset.filter(status=Invoice.InvoiceStatus.PENDING)
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = InvoiceListSerializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def paid(self, request):
        """Get paid invoices."""
        invoices = self.queryset.filter(status=Invoice.InvoiceStatus.PAID)
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = InvoiceListSerializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def patient_invoices(self, request):
        """Get invoices for a specific patient."""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {"error": "Patient ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoices = self.queryset.filter(patient_id=patient_id)
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = InvoiceListSerializer(invoices, many=True)
        return Response(serializer.data)
    
    # Thêm các action liên quan đến xuất báo cáo hóa đơn
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Xuất danh sách hóa đơn ra file CSV"""

        # Tạo response với header phù hợp
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invoices.csv"'
        
        # Tạo writer CSV
        writer = csv.writer(response)
        writer.writerow(['Số hóa đơn', 'Ngày', 'Bệnh nhân', 'Trạng thái', 'Tổng tiền'])
        
        # Lấy dữ liệu hóa đơn
        invoices = self.filter_queryset(self.get_queryset())
        for invoice in invoices:
            writer.writerow([
                invoice.invoice_number,
                invoice.invoice_date,
                invoice.patient.full_name,
                invoice.get_status_display(),
                invoice.total
            ])
        
        return response

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Thống kê hóa đơn theo thời gian"""
        # Lấy thông số từ request
        period = request.query_params.get('period', 'month')
        
        # Xác định khoảng thời gian
        today = timezone.now().date()
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'month':
            start_date = today - timedelta(days=30)
        elif period == 'quarter':
            start_date = today - timedelta(days=90)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=30)  # Mặc định là tháng
        
        # Tính tổng số hóa đơn và doanh thu
        invoices = Invoice.objects.filter(invoice_date__gte=start_date)
        stats = {
            'period': period,
            'start_date': start_date,
            'end_date': today,
            'total_count': invoices.count(),
            'total_revenue': invoices.aggregate(total=Sum('total'))['total'] or 0,
            'paid_count': invoices.filter(status=Invoice.InvoiceStatus.PAID).count(),
            'paid_revenue': invoices.filter(status=Invoice.InvoiceStatus.PAID).aggregate(total=Sum('total'))['total'] or 0,
            'pending_count': invoices.filter(status=Invoice.InvoiceStatus.PENDING).count(),
            'pending_revenue': invoices.filter(status=Invoice.InvoiceStatus.PENDING).aggregate(total=Sum('total'))['total'] or 0,
        }
        
        return Response(stats)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentFilter
    filterset_fields = ['invoice', 'payment_method', 'payment_date']
    search_fields = ['reference_number', 'invoice__invoice_number', 'invoice__patient__full_name']
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']

    def get_serializer_class(self):
        """Return different serializers based on action."""
        if self.action == 'list':
            return PaymentListSerializer
        return PaymentSerializer

    def get_permissions(self):
        """
        Only admin and staff can manage payments.
        """
        permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Set the staff to the current user when creating a payment."""
        serializer.save(staff=self.request.user)
    
    @action(detail=False)
    def invoice_payments(self, request):
        """Get payments for a specific invoice."""
        invoice_id = request.query_params.get('invoice_id')
        if not invoice_id:
            return Response(
                {"error": "Invoice ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payments = self.queryset.filter(invoice_id=invoice_id)
        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
# Tạo view để in hóa đơn
class InvoicePrintView(View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        
        # Lấy danh sách dịch vụ
        services = ExaminationService.objects.filter(examination=invoice.examination)
        
        # Lấy danh sách thuốc nếu có
        medicines = []
        try:
            if hasattr(invoice.examination, 'prescription'):
                medicines = PrescriptionItem.objects.filter(
                    prescription=invoice.examination.prescription
                )
        except:
            pass
        
        context = {
            'invoice': invoice,
            'services': services,
            'medicines': medicines
        }
        
        return render(request, 'billing/invoice_print.html', context)