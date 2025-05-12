from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DentalServiceViewSet,
    MedicalRecordViewSet,
    ExaminationViewSet,
    ExaminationServiceViewSet
)

# Tạo router để quản lý các viewset
router = DefaultRouter()
router.register(r'services', DentalServiceViewSet, basename='dental-service')
router.register(r'records', MedicalRecordViewSet, basename='medical-record')
router.register(r'examinations', ExaminationViewSet, basename='examination')
router.register(r'examination-services', ExaminationServiceViewSet, basename='examination-service')

urlpatterns = [
    # Bao gồm các URL từ router
    path('', include(router.urls)),
]