from rest_framework import serializers
from .models import Medicine, Prescription, PrescriptionItem, MedicineStock
from medical_records.serializers import ExaminationSerializer


class MedicineSerializer(serializers.ModelSerializer):
    """Serializer for Medicine model."""
    
    class Meta:
        model = Medicine
        fields = ('id', 'code', 'name', 'unit', 'indication', 'quantity_in_stock',
                  'expiry_date', 'price', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """Serializer for PrescriptionItem model."""
    
    medicine_detail = MedicineSerializer(source='medicine', read_only=True)
    
    class Meta:
        model = PrescriptionItem
        fields = ('id', 'prescription', 'medicine', 'medicine_detail',
                  'quantity', 'dosage', 'instructions', 'price')
        read_only_fields = ('id',)


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for Prescription model."""
    
    items = PrescriptionItemSerializer(many=True, read_only=True)
    examination_detail = ExaminationSerializer(source='examination', read_only=True)
    
    class Meta:
        model = Prescription
        fields = ('id', 'examination', 'examination_detail', 'prescription_date',
                  'notes', 'items')
        read_only_fields = ('id', 'prescription_date')


class PrescriptionItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PrescriptionItem instances."""
    
    class Meta:
        model = PrescriptionItem
        fields = ('medicine', 'quantity', 'dosage', 'instructions')
    
    def validate_medicine(self, value):
        """Validate that the medicine exists and is active."""
        try:
            medicine = Medicine.objects.get(id=value.id, is_active=True)
            if medicine.quantity_in_stock < self.initial_data.get('quantity', 0):
                raise serializers.ValidationError("Số lượng thuốc trong kho không đủ.")
            return value
        except Medicine.DoesNotExist:
            raise serializers.ValidationError("Thuốc không tồn tại hoặc không còn được sử dụng.")


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Prescription with nested items."""
    
    items = PrescriptionItemCreateSerializer(many=True)
    
    class Meta:
        model = Prescription
        fields = ('examination', 'notes', 'items')
    
    def create(self, validated_data):
        """Create a prescription with nested items and update medicine stock."""
        items_data = validated_data.pop('items', [])
        prescription = Prescription.objects.create(**validated_data)
        
        for item_data in items_data:
            medicine = item_data.pop('medicine')
            quantity = item_data.get('quantity')
            
            # Create prescription item
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine=medicine,
                price=medicine.price,
                **item_data
            )
            
            # Update medicine stock
            medicine.quantity_in_stock -= quantity
            medicine.save()
            
            # Create stock record
            MedicineStock.objects.create(
                medicine=medicine,
                quantity=-quantity,
                stock_type=MedicineStock.StockType.EXPORT,
                reference=f"Prescription-{prescription.id}",
                notes=f"Xuất thuốc theo đơn thuốc cho bệnh nhân {prescription.examination.medical_record.patient.full_name}"
            )
        
        return prescription


class MedicineStockSerializer(serializers.ModelSerializer):
    """Serializer for MedicineStock model."""
    
    medicine_detail = MedicineSerializer(source='medicine', read_only=True)
    stock_type_display = serializers.CharField(source='get_stock_type_display', read_only=True)
    
    class Meta:
        model = MedicineStock
        fields = ('id', 'medicine', 'medicine_detail', 'quantity', 'stock_type',
                  'stock_type_display', 'reference', 'notes', 'created_at')
        read_only_fields = ('id', 'created_at', 'stock_type_display')


class MedicineImportSerializer(serializers.Serializer):
    """Serializer for importing medicine to stock."""
    
    medicine_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    reference = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_medicine_id(self, value):
        """Validate that the medicine exists."""
        try:
            return Medicine.objects.get(id=value, is_active=True)
        except Medicine.DoesNotExist:
            raise serializers.ValidationError("Thuốc không tồn tại hoặc không còn được sử dụng.")
    
    def create(self, validated_data):
        """Import medicine to stock."""
        medicine = validated_data.pop('medicine_id')
        quantity = validated_data.get('quantity')
        
        # Update medicine stock
        medicine.quantity_in_stock += quantity
        medicine.save()
        
        # Create stock record
        stock_record = MedicineStock.objects.create(
            medicine=medicine,
            quantity=quantity,
            stock_type=MedicineStock.StockType.IMPORT,
            reference=validated_data.get('reference', ''),
            notes=validated_data.get('notes', '')
        )
        
        return stock_record