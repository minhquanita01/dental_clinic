from rest_framework import serializers
from .models import DentalService, MedicalRecord, Examination, ExaminationService
from accounts.serializers import UserPublicSerializer
from accounts.models import User


class DentalServiceSerializer(serializers.ModelSerializer):
    """Serializer for DentalService model."""
    
    class Meta:
        model = DentalService
        fields = ('id', 'name', 'description', 'price')
        read_only_fields = ('id',)


class ExaminationServiceSerializer(serializers.ModelSerializer):
    """Serializer for ExaminationService model."""
    
    service_detail = DentalServiceSerializer(source='service', read_only=True)
    
    class Meta:
        model = ExaminationService
        fields = ('id', 'examination', 'service', 'service_detail', 'quantity', 'price', 'notes')
        read_only_fields = ('id',)


class ExaminationSerializer(serializers.ModelSerializer):
    """Serializer for Examination model."""
    
    dentist_detail = UserPublicSerializer(source='dentist', read_only=True)
    services = ExaminationServiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Examination
        fields = ('id', 'medical_record', 'appointment', 'dentist', 'dentist_detail',
                  'examination_date', 'diagnosis', 'treatment_plan', 'notes', 'services')
        read_only_fields = ('id',)


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRecord model."""
    
    patient_detail = UserPublicSerializer(source='patient', read_only=True)
    examinations = ExaminationSerializer(many=True, read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = ('id', 'patient', 'patient_detail', 'created_at', 'updated_at',
                  'notes', 'examinations')
        read_only_fields = ('id', 'created_at', 'updated_at')


class ExaminationServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ExaminationService instances."""
    
    class Meta:
        model = ExaminationService
        fields = ('service', 'quantity', 'notes')
    
    def validate_service(self, value):
        """Validate that the service exists."""
        if not DentalService.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Dịch vụ không tồn tại.")
        return value


class ExaminationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Examination with nested services."""
    
    services = ExaminationServiceCreateSerializer(many=True)
    
    class Meta:
        model = Examination
        fields = ('medical_record', 'appointment', 'dentist', 'examination_date',
                  'diagnosis', 'treatment_plan', 'notes', 'services')
    
    def validate_medical_record(self, value):
        """Validate that the medical record exists."""
        if not MedicalRecord.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Hồ sơ bệnh án không tồn tại.")
        return value
    
    def validate_dentist(self, value):
        """Validate that the user is a dentist."""
        if value.user_type != User.UserType.DENTIST:
            raise serializers.ValidationError("Người dùng không phải là nha sĩ.")
        return value
    
    def create(self, validated_data):
        """Create an examination with nested services."""
        services_data = validated_data.pop('services', [])
        examination = Examination.objects.create(**validated_data)
        
        for service_data in services_data:
            service = service_data.pop('service')
            ExaminationService.objects.create(
                examination=examination,
                service=service,
                price=service.price,
                **service_data
            )
        
        return examination