from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentViewSet, 
    DentistScheduleViewSet, 
    DentistTimeOffViewSet
)

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'dentist-schedules', DentistScheduleViewSet, basename='dentist-schedule')
router.register(r'dentist-time-offs', DentistTimeOffViewSet, basename='dentist-time-off')

urlpatterns = [
    path('', include(router.urls)),
]