from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MedicineViewSet, PrescriptionViewSet, MedicineStockViewSet

# Tạo router để đăng ký các ViewSet
router = DefaultRouter()
router.register(r'medicines', MedicineViewSet, basename='medicine')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'medicine-stocks', MedicineStockViewSet, basename='medicine-stock')

urlpatterns = [
    # Bao gồm các URL từ router
    path('', include(router.urls)),
]