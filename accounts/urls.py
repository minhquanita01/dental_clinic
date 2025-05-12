from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, CustomerRegistrationView, 
    UserViewSet, DentistViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'dentists', DentistViewSet, basename='dentist')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', CustomerRegistrationView.as_view(), name='register'),
]