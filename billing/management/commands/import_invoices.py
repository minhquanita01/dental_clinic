import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from medical_records.models import Examination, MedicalRecord
from billing.models import Invoice

class Command(BaseCommand):
    help = 'Import invoices from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['csv_file']
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from {file_path}'))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                with transaction.atomic():
                    for row in reader:
                        try:
                            # Tìm bệnh nhân theo số điện thoại
                            patient = User.objects.get(phone_number=row['patient_phone'])
                            
                            # Tìm hồ sơ bệnh án
                            medical_record = MedicalRecord.objects.get(patient=patient)
                            
                            # Tìm lần khám gần nhất
                            examination = Examination.objects.filter(
                                medical_record=medical_record
                            ).order_by('-examination_date').first()
                            
                            if not examination:
                                self.stdout.write(self.style.WARNING(
                                    f'No examination found for patient {patient.full_name}'
                                ))
                                continue
                            
                            # Kiểm tra xem đã có hóa đơn chưa
                            if hasattr(examination, 'invoice'):
                                self.stdout.write(self.style.WARNING(
                                    f'Invoice already exists for examination {examination.id}'
                                ))
                                continue
                            
                            # Tạo invoice number
                            last_invoice = Invoice.objects.order_by('-id').first()
                            invoice_number = f"INV-{(last_invoice.id + 1 if last_invoice else 1):06d}"
                            
                            # Tạo hóa đơn mới
                            invoice = Invoice.objects.create(
                                examination=examination,
                                patient=patient,
                                staff=examination.dentist,  # Lấy nha sĩ từ lần khám
                                invoice_number=invoice_number,
                                status=Invoice.InvoiceStatus.PENDING
                            )
                            
                            # Cập nhật giá trị từ CSV nếu có
                            if 'discount' in row and row['discount']:
                                invoice.discount = float(row['discount'])
                            
                            if 'tax' in row and row['tax']:
                                invoice.tax = float(row['tax'])
                            
                            # Tính toán tổng
                            invoice.calculate_totals()
                            
                            self.stdout.write(self.style.SUCCESS(
                                f'Created invoice {invoice.invoice_number} for patient {patient.full_name}'
                            ))
                        
                        except User.DoesNotExist:
                            self.stdout.write(self.style.ERROR(
                                f'Patient not found with phone: {row["patient_phone"]}'
                            ))
                        
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f'Error processing row: {row}. Error: {str(e)}'
                            ))
            
            self.stdout.write(self.style.SUCCESS('Import completed'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to import data: {str(e)}'))