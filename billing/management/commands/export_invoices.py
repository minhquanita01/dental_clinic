import csv
import os
from django.core.management.base import BaseCommand
from billing.models import Invoice

class Command(BaseCommand):
    help = 'Export invoices to CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, default='invoices_export.csv', 
                           help='Output file path')
        parser.add_argument('--status', type=str, choices=['PENDING', 'PAID', 'CANCELLED', 'ALL'],
                           default='ALL', help='Invoice status to export')

    def handle(self, *args, **options):
        output_file = options['output']
        status = options['status']
        
        # Lọc hóa đơn theo trạng thái
        if status == 'ALL':
            invoices = Invoice.objects.all()
        else:
            invoices = Invoice.objects.filter(status=status)
        
        try:
            with open(output_file, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                
                # Viết header
                writer.writerow([
                    'Số hóa đơn', 'Ngày', 'Bệnh nhân', 'Điện thoại', 
                    'Nha sĩ', 'Dịch vụ', 'Tổng tiền dịch vụ', 'Tổng tiền thuốc',
                    'Giảm giá', 'Thuế', 'Tổng cộng', 'Trạng thái'
                ])
                
                # Viết dữ liệu
                for invoice in invoices:
                    services = ', '.join([
                        f"{service.service.name} ({service.quantity})" 
                        for service in invoice.examination.examination_services.all()
                    ])
                    
                    writer.writerow([
                        invoice.invoice_number,
                        invoice.invoice_date,
                        invoice.patient.full_name,
                        invoice.patient.phone_number,
                        invoice.examination.dentist.full_name,
                        services,
                        invoice.subtotal,
                        invoice.medicine_total,
                        invoice.discount,
                        invoice.tax,
                        invoice.total,
                        invoice.get_status_display()
                    ])
            
            abs_path = os.path.abspath(output_file)
            self.stdout.write(self.style.SUCCESS(f'Successfully exported {invoices.count()} invoices to {abs_path}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to export data: {str(e)}'))