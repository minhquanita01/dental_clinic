from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import (
    DentalService, 
    MedicalRecord, 
    Examination, 
    ExaminationService
)
from .serializers import (
    DentalServiceSerializer,
    MedicalRecordSerializer,
    ExaminationSerializer,
    ExaminationCreateSerializer,
    ExaminationServiceSerializer
)
from accounts.models import User


class DentalServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing dental services."""
    queryset = DentalService.objects.all()
    serializer_class = DentalServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Custom permission logic:
        - Staff and Admin can perform all operations
        - Other authenticated users can only list and retrieve
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class MedicalRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for medical records with custom actions."""
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Customize queryset based on user type:
        - Admin and Staff can see all records
        - Dentists can see their patients' records
        - Customers can only see their own record
        """
        user = self.request.user
        if user.user_type in [User.UserType.ADMIN, User.UserType.STAFF]:
            return MedicalRecord.objects.all()
        elif user.user_type == User.UserType.DENTIST:
            # Dentists can see records of patients they've examined
            return MedicalRecord.objects.filter(
                examinations__dentist=user
            ).distinct()
        elif user.user_type == User.UserType.CUSTOMER:
            # Customers can only see their own record
            return MedicalRecord.objects.filter(patient=user)
        return MedicalRecord.objects.none()

    @action(detail=False, methods=['GET'], url_path='my-record')
    def get_current_user_record(self, request):
        """
        Get the medical record for the current user.
        Only works for customers.
        """
        if request.user.user_type != User.UserType.CUSTOMER:
            return Response(
                {"detail": "This action is only available for customers."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            record = MedicalRecord.objects.get(patient=request.user)
            serializer = self.get_serializer(record)
            return Response(serializer.data)
        except MedicalRecord.DoesNotExist:
            return Response(
                {"detail": "No medical record found."},
                status=status.HTTP_404_NOT_FOUND
            )


class ExaminationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing patient examinations."""
    queryset = Examination.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Use different serializers for different actions.
        Create action uses a special create serializer.
        """
        if self.action == 'create':
            return ExaminationCreateSerializer
        return ExaminationSerializer

    def get_queryset(self):
        """
        Customize queryset based on user type:
        - Admin and Staff can see all examinations
        - Dentists can see examinations they performed
        - Customers can see their own examinations
        """
        user = self.request.user
        if user.user_type in [User.UserType.ADMIN, User.UserType.STAFF]:
            return Examination.objects.all()
        elif user.user_type == User.UserType.DENTIST:
            return Examination.objects.filter(dentist=user)
        elif user.user_type == User.UserType.CUSTOMER:
            return Examination.objects.filter(medical_record__patient=user)
        return Examination.objects.none()

    def perform_create(self, serializer):
        """
        Ensure the dentist creating the examination is the current user.
        """
        serializer.save(dentist=self.request.user)

    @action(detail=True, methods=['GET'], url_path='services')
    def get_examination_services(self, request, pk=None):
        """
        Get all services for a specific examination.
        """
        examination = self.get_object()
        services = examination.services.all()
        serializer = ExaminationServiceSerializer(services, many=True)
        return Response(serializer.data)


class ExaminationServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for examination services."""
    queryset = ExaminationService.objects.all()
    serializer_class = ExaminationServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Customize queryset based on user type:
        - Admin and Staff can see all examination services
        - Dentists can see services from their examinations
        - Customers can see services from their own examinations
        """
        user = self.request.user
        if user.user_type in [User.UserType.ADMIN, User.UserType.STAFF]:
            return ExaminationService.objects.all()
        elif user.user_type == User.UserType.DENTIST:
            return ExaminationService.objects.filter(examination__dentist=user)
        elif user.user_type == User.UserType.CUSTOMER:
            return ExaminationService.objects.filter(
                examination__medical_record__patient=user
            )
        return ExaminationService.objects.none()