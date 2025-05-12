from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'
    verbose_name = 'Quản lý hóa đơn và thanh toán'

    def ready(self):
        import billing.signals  # Import signals khi app khởi động