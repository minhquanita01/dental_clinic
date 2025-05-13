from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch

from accounts.models import User
from medical_records.models import MedicalRecord, Examination, DentalService, ExaminationService
from .models import Invoice, Payment

# Create your tests here.
class InvoiceAPITestCase(TestCase):

    def setUp(self):
        # Tạo người dùng
        self.admin = User.objects.create_user(
            phone_number='0901234567',
            full_name='Admin User',
            password='password123',
            user_type=User.UserType.ADMIN
        )
        
        self.staff = User.objects.create_user(
            phone_number='0901234568',
            full_name='Staff User',
            password='password123',
            user_type=User.UserType.STAFF
        )
        
        self.dentist = User.objects.create_user(
            phone_number='0901234569',
            full_name='Dentist User',
            password='password123',
            user_type=User.UserType.DENTIST
        )
        
        self.patient = User.objects.create_user(
            phone_number='0901234570',
            full_name='Patient User',
            password='password123',
            user_type=User.UserType.CUSTOMER
        )
        
        # Tạo hồ sơ bệnh án
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient,
            notes='Patient medical record'
        )
        
        # Tạo dịch vụ nha khoa
        self.service = DentalService.objects.create(
            name='Khám răng',
            description='Kiểm tra sức khỏe răng miệng',
            price=200000
        )
        
        # Tạo lần khám
        self.examination = Examination.objects.create(
            medical_record=self.medical_record,
            dentist=self.dentist,
            examination_date=date.today(),
            diagnosis='Răng khỏe mạnh',
            treatment_plan='Không cần điều trị'
        )
        
        # Tạo dịch vụ đã sử dụng
        self.exam_service = ExaminationService.objects.create(
            examination=self.examination,
            service=self.service,
            quantity=1,
            price=200000
        )

        # Sử dụng patch để ghi đè hàm tạo số hóa đơn
        with patch('billing.models.Invoice.generate_invoice_number') as mock_generate:
            # Trả về số hóa đơn duy nhất cho mỗi lần test
            mock_generate.return_value = f"INV-TEST-{self._testMethodName}"
            
            # Bây giờ việc tạo hóa đơn sẽ sử dụng hàm tạo số hóa đơn đã được ghi đè
            self.invoice = Invoice.objects.create(
                examination=self.examination,
                patient=self.patient,
                staff=self.staff,
                status=Invoice.InvoiceStatus.PENDING,
                discount=0,
                tax=0
            )

        # Tính toán tổng tiền hóa đơn
        self.invoice.calculate_totals()
        
        # Tạo client API
        self.client = APIClient()
    
    def test_get_invoices_list_unauthenticated(self):
        """Test that unauthenticated users cannot access invoices."""
        url = reverse('invoice-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_invoices_list_authenticated_staff(self):
        """Test that staff users can access invoices."""
        url = reverse('invoice-list')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_create_invoice(self):
        """Test creating a new invoice."""
        url = reverse('invoice-list')
        self.client.force_authenticate(user=self.staff)
        
        # Tạo một lần khám mới cho invoice mới
        new_examination = Examination.objects.create(
            medical_record=self.medical_record,
            dentist=self.dentist,
            examination_date=date.today() - timedelta(days=1),  # Ngày khác để tránh trùng lặp
            diagnosis='Dental check',
            treatment_plan='No treatment needed'
        )
        
        data = {
            'examination': new_examination.id,
            'patient': self.patient.id,
            'invoice_number': f'INV-000042-{self._testMethodName}',  # Đảm bảo duy nhất
            'status': Invoice.InvoiceStatus.PENDING,
            'discount': 10000,
            'tax': 5000,
            'notes': 'Test invoice'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the invoice was created
        invoice_id = response.data['id']
        invoice = Invoice.objects.get(id=invoice_id)
        self.assertEqual(invoice.patient, self.patient)
        self.assertEqual(invoice.staff, self.staff)
        self.assertEqual(invoice.status, Invoice.InvoiceStatus.PENDING)
    
    def test_calculate_totals(self):
        """Test recalculating invoice totals."""
        url = reverse('invoice-calculate-totals', args=[self.invoice.id])
        self.client.force_authenticate(user=self.staff)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify totals
        self.assertEqual(Decimal(response.data['subtotal']), Decimal('200000'))
        self.assertEqual(Decimal(response.data['total']), Decimal('200000'))
    
    def test_pending_invoices(self):
        """Test getting pending invoices."""
        url = reverse('invoice-pending')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class PaymentAPITestCase(TestCase):

    def setUp(self):
        # Create needed instances from the previous test case
        self.admin = User.objects.create_user(
            phone_number='0911234567',  # Changed to avoid duplicate phone numbers
            full_name='Admin User Payment',
            password='password123',
            user_type=User.UserType.ADMIN
        )
        
        self.staff = User.objects.create_user(
            phone_number='0911234568',  # Changed to avoid duplicate phone numbers
            full_name='Staff User Payment',
            password='password123',
            user_type=User.UserType.STAFF
        )
        
        self.patient = User.objects.create_user(
            phone_number='0911234570',  # Changed to avoid duplicate phone numbers
            full_name='Patient User Payment',
            password='password123',
            user_type=User.UserType.CUSTOMER
        )
        
        self.dentist = User.objects.create_user(
            phone_number='0911234569',  # Changed to avoid duplicate phone numbers
            full_name='Dentist User Payment',
            password='password123',
            user_type=User.UserType.DENTIST
        )
        
        # Tạo hồ sơ bệnh án riêng biệt cho test này
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient,
            notes='Patient medical record for payment test'
        )
        
        # Tạo dịch vụ nha khoa
        self.service = DentalService.objects.create(
            name='Khám răng payment',
            description='Kiểm tra sức khỏe răng miệng cho payment test',
            price=200000
        )
        
        # Tạo lần khám MỚI và riêng biệt
        self.examination = Examination.objects.create(
            medical_record=self.medical_record,
            dentist=self.dentist,
            examination_date=date.today() - timedelta(days=7),  # Ngày khác để tránh trùng lặp
            diagnosis='Test cho payment',
            treatment_plan='Payment test'
        )
        
        # Tạo dịch vụ đã sử dụng
        self.exam_service = ExaminationService.objects.create(
            examination=self.examination,
            service=self.service,
            quantity=1,
            price=200000
        )
        
        with patch('billing.models.Invoice.generate_invoice_number') as mock_generate:
            # Trả về số hóa đơn duy nhất cho mỗi lần test
            # Phần này sử dụng tên phương thức kiểm tra để đảm bảo tính duy nhất
            mock_generate.return_value = f"INV-PAYMENT-{self._testMethodName}"
            
            # Bây giờ việc tạo hóa đơn sẽ sử dụng hàm tạo số hóa đơn đã được ghi đè
            self.invoice = Invoice.objects.create(
                examination=self.examination,
                patient=self.patient,
                staff=self.staff,
                status=Invoice.InvoiceStatus.PENDING,
                discount=0,
                tax=0
            )

        self.invoice.calculate_totals()
        
        # Create a payment
        self.payment = Payment.objects.create(
            invoice=self.invoice,
            amount=100000,
            payment_method=Payment.PaymentMethod.CASH,
            reference_number='REF123',
            staff=self.staff,
            notes='Partial payment'
        )
        
        # Set up the API client
        self.client = APIClient()
    
    def test_get_payments_list_authenticated_staff(self):
        """Test that staff users can access payments."""
        url = reverse('payment-list')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_create_payment(self):
        """Test creating a new payment."""
        url = reverse('payment-list')
        self.client.force_authenticate(user=self.staff)
        
        data = {
            'invoice': self.invoice.id,
            'amount': 100000,
            'payment_method': Payment.PaymentMethod.CARD,
            'reference_number': 'CARD123',
            'notes': 'Test payment'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the payment was created
        payment_id = response.data['id']
        payment = Payment.objects.get(id=payment_id)
        self.assertEqual(payment.invoice, self.invoice)
        self.assertEqual(payment.amount, Decimal('100000'))
        self.assertEqual(payment.staff, self.staff)
        
        # Verify invoice status changed to PAID since total was paid
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.InvoiceStatus.PAID)
    
    def test_payment_validation_exceeds_remaining(self):
        """Test that payment amount cannot exceed remaining balance."""
        url = reverse('payment-list')
        self.client.force_authenticate(user=self.staff)
        
        data = {
            'invoice': self.invoice.id,
            'amount': 300000,  # More than remaining 100000
            'payment_method': Payment.PaymentMethod.CASH,
            'reference_number': 'OVER123',
            'notes': 'Overpayment'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_invoice_payments(self):
        """Test getting payments for a specific invoice."""
        url = reverse('payment-invoice-payments') + f'?invoice_id={self.invoice.id}'
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)