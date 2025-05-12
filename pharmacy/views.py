from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Medicine, Prescription, PrescriptionItem, MedicineStock
from .serializers import (
    MedicineSerializer, 
    PrescriptionSerializer, 
    PrescriptionCreateSerializer,
    MedicineStockSerializer,
    MedicineImportSerializer
)
from accounts.permissions import IsDentistOrAdmin, IsStaffOrAdmin


class MedicineViewSet(viewsets.ModelViewSet):
    """ViewSet for managing medicines."""
    
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    
    def get_queryset(self):
        """
        Optionally filter medicines based on query parameters.
        """
        queryset = Medicine.objects.all()
        name = self.request.query_params.get('name')
        is_active = self.request.query_params.get('is_active')
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset
    
    @action(detail=False, methods=['GET'], url_path='low-stock')
    def low_stock_medicines(self, request):
        """
        Retrieve medicines with low stock (quantity less than a threshold).
        """
        threshold = int(request.query_params.get('threshold', 10))
        low_stock_medicines = Medicine.objects.filter(quantity_in_stock__lt=threshold)
        serializer = self.get_serializer(low_stock_medicines, many=True)
        return Response(serializer.data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing prescriptions."""
    
    queryset = Prescription.objects.all()
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions.
        """
        if self.action == 'create':
            return PrescriptionCreateSerializer
        return PrescriptionSerializer
    
    def get_queryset(self):
        """
        Optionally filter prescriptions based on query parameters.
        """
        queryset = Prescription.objects.all()
        patient_id = self.request.query_params.get('patient_id')
        
        if patient_id:
            queryset = queryset.filter(examination__medical_record__patient_id=patient_id)
        
        return queryset


class MedicineStockViewSet(viewsets.ModelViewSet):
    """ViewSet for managing medicine stock records."""
    
    queryset = MedicineStock.objects.all()
    serializer_class = MedicineStockSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    
    def get_queryset(self):
        """
        Optionally filter stock records based on query parameters.
        """
        queryset = MedicineStock.objects.all()
        medicine_id = self.request.query_params.get('medicine_id')
        stock_type = self.request.query_params.get('stock_type')
        
        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)
        
        if stock_type:
            queryset = queryset.filter(stock_type=stock_type)
        
        return queryset
    
    @action(detail=False, methods=['POST'], url_path='import')
    def import_medicine(self, request):
        """
        Import medicine to stock.
        """
        serializer = MedicineImportSerializer(data=request.data)
        if serializer.is_valid():
            stock_record = serializer.save()
            return Response(
                MedicineStockSerializer(stock_record).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)