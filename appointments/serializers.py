from rest_framework import serializers
from datetime import date, datetime, timedelta
from django.utils import timezone
from .models import Appointment, DentistSchedule, DentistTimeOff
from accounts.serializers import UserPublicSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model."""
    
    patient_detail = UserPublicSerializer(source='patient', read_only=True)
    dentist_detail = UserPublicSerializer(source='dentist', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ('id', 'patient', 'patient_detail', 'dentist', 'dentist_detail',
                  'appointment_date', 'appointment_time', 'reason', 'status',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, data):
        """Custom validation for appointment creation."""
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        dentist = data.get('dentist')
        
        # Check if date is in the past
        if appointment_date < date.today():
            raise serializers.ValidationError({"appointment_date": "Không thể đặt lịch hẹn trong quá khứ."})
        
        # Check if date is too far in the future (e.g., more than 3 months)
        if appointment_date > date.today() + timedelta(days=90):
            raise serializers.ValidationError({"appointment_date": "Không thể đặt lịch hẹn xa quá 3 tháng."})
        
        # Check if dentist is on time off
        time_offs = DentistTimeOff.objects.filter(
            dentist=dentist,
            start_date__lte=appointment_date,
            end_date__gte=appointment_date
        )
        if time_offs.exists():
            raise serializers.ValidationError({"dentist": "Nha sĩ không làm việc vào ngày này."})
        
        # Check dentist schedule for the day
        weekday = appointment_date.weekday()
        schedules = DentistSchedule.objects.filter(
            dentist=dentist,
            weekday=weekday,
            is_available=True
        )
        
        valid_time = False
        for schedule in schedules:
            if schedule.start_time <= appointment_time <= schedule.end_time:
                valid_time = True
                break
        
        if not valid_time and schedules.exists():
            raise serializers.ValidationError({"appointment_time": "Thời gian không nằm trong lịch làm việc của nha sĩ."})
        elif not schedules.exists():
            raise serializers.ValidationError({"appointment_date": "Nha sĩ không làm việc vào ngày này."})
        
        # Check for conflicting appointments
        existing_appointments = Appointment.objects.filter(
            dentist=dentist,
            appointment_date=appointment_date,
            status__in=[Appointment.AppointmentStatus.PENDING, Appointment.AppointmentStatus.CONFIRMED]
        )
        
        # Consider appointment duration to be 30 minutes
        appointment_end_time = (
            datetime.combine(date.today(), appointment_time) + timedelta(minutes=30)
        ).time()
        
        for existing in existing_appointments:
            existing_end_time = (
                datetime.combine(date.today(), existing.appointment_time) + timedelta(minutes=30)
            ).time()
            
            if (appointment_time <= existing.appointment_time < appointment_end_time or
                appointment_time < existing_end_time <= appointment_end_time or
                existing.appointment_time <= appointment_time < existing_end_time):
                raise serializers.ValidationError({
                    "appointment_time": "Nha sĩ đã có lịch hẹn khác trong khung giờ này."
                })
        
        return data


class DentistScheduleSerializer(serializers.ModelSerializer):
    """Serializer for DentistSchedule model."""
    
    dentist_detail = UserPublicSerializer(source='dentist', read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = DentistSchedule
        fields = ('id', 'dentist', 'dentist_detail', 'weekday', 'weekday_display',
                  'start_time', 'end_time', 'is_available')
        read_only_fields = ('id', 'weekday_display')
    
    def validate(self, data):
        """Validate schedule time consistency."""
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError({
                "end_time": "Thời gian kết thúc phải sau thời gian bắt đầu."
            })
        return data


class DentistTimeOffSerializer(serializers.ModelSerializer):
    """Serializer for DentistTimeOff model."""
    
    dentist_detail = UserPublicSerializer(source='dentist', read_only=True)
    
    class Meta:
        model = DentistTimeOff
        fields = ('id', 'dentist', 'dentist_detail', 'start_date', 'end_date', 'reason')
        read_only_fields = ('id',)
    
    def validate(self, data):
        """Validate date consistency."""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError({
                "end_date": "Ngày kết thúc phải sau ngày bắt đầu."
            })
        
        if data['start_date'] < date.today():
            raise serializers.ValidationError({
                "start_date": "Ngày bắt đầu không thể nằm trong quá khứ."
            })
            
        return data