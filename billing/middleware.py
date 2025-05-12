import logging
from django.utils import timezone

logger = logging.getLogger('billing')

class BillingLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Xử lý trước khi view được gọi
        response = self.get_response(request)
        
        # Ghi log các hoạt động liên quan đến thanh toán
        if request.path.startswith('/api/billing/') and request.method in ['POST', 'PUT', 'DELETE']:
            if request.user.is_authenticated:
                logger.info(
                    f"[{timezone.now()}] User {request.user.username} performed {request.method} on {request.path}"
                )
        
        return response