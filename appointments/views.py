from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models import Appointment, DentistSchedule, DentistTimeOff
from .serializers import (
    AppointmentSerializer, 
    DentistScheduleSerializer, 
    DentistTimeOffSerializer
)
from accounts.permissions import (
    IsAdminUser, 
    IsDentistUser, 
    IsCustomerUser, 
    IsStaffUser
)


class AppointmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing appointments."""
    
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'list':
            permission_classes = [IsAdminUser | IsStaffUser | IsDentistUser]
        elif self.action == 'create':
            permission_classes = [IsCustomerUser | IsStaffUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser | IsStaffUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Customize queryset based on user type."""
        user = self.request.user
        
        if user.user_type == user.UserType.CUSTOMER:
            return Appointment.objects.filter(patient=user)
        elif user.user_type == user.UserType.DENTIST:
            return Appointment.objects.filter(dentist=user)
        elif user.user_type in [user.UserType.STAFF, user.UserType.ADMIN]:
            return Appointment.objects.all()
        
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'], permission_classes=[IsDentistUser])
    def my_appointments(self, request):
        """Get appointments for the current dentist."""
        queryset = self.get_queryset().filter(
            dentist=request.user, 
            status__in=[
                Appointment.AppointmentStatus.PENDING, 
                Appointment.AppointmentStatus.CONFIRMED
            ]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsStaffUser | IsAdminUser])
    def update_status(self, request, pk=None):
        """Update appointment status."""
        try:
            appointment = self.get_object()
            new_status = request.data.get('status')
            
            if new_status not in dict(Appointment.AppointmentStatus.choices):
                return Response(
                    {'error': 'Trạng thái không hợp lệ'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            appointment.status = new_status
            appointment.save()
            
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Không tìm thấy lịch hẹn'},
                status=status.HTTP_404_NOT_FOUND
            )


class DentistScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing dentist schedules."""
    
    queryset = DentistSchedule.objects.all()
    serializer_class = DentistScheduleSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminUser | IsDentistUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Customize queryset based on user type."""
        user = self.request.user
        
        if user.user_type == user.UserType.DENTIST:
            return DentistSchedule.objects.filter(dentist=user)
        elif user.user_type in [user.UserType.STAFF, user.UserType.ADMIN]:
            return DentistSchedule.objects.all()
        
        return DentistSchedule.objects.none()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser | IsDentistUser])
    def availability(self, request):
        """Get available time slots for a given date."""
        date_str = request.query_params.get('date')
        dentist_id = request.query_params.get('dentist')
        
        if not date_str or not dentist_id:
            return Response(
                {'error': 'Vui lòng cung cấp ngày và nha sĩ'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            weekday = selected_date.weekday()
            
            # Get dentist's schedule for the specific day
            schedules = DentistSchedule.objects.filter(
                dentist_id=dentist_id, 
                weekday=weekday, 
                is_available=True
            )
            
            # Get existing appointments on this day
            existing_appointments = Appointment.objects.filter(
                dentist_id=dentist_id,
                appointment_date=selected_date,
                status__in=[
                    Appointment.AppointmentStatus.PENDING, 
                    Appointment.AppointmentStatus.CONFIRMED
                ]
            )
            
            # Get dentist's time off
            time_offs = DentistTimeOff.objects.filter(
                dentist_id=dentist_id,
                start_date__lte=selected_date,
                end_date__gte=selected_date
            )
            
            if time_offs.exists():
                return Response({'available_slots': []})
            
            available_slots = []
            for schedule in schedules:
                current_time = schedule.start_time
                while current_time < schedule.end_time:
                    # Check if this time slot is available
                    conflict = existing_appointments.filter(
                        Q(appointment_time__lte=current_time) & 
                        Q(appointment_time__gt=(
                            timezone.datetime.combine(timezone.datetime.today(), current_time) - 
                            timezone.timedelta(minutes=30)
                        ).time())
                    ).exists()
                    
                    if not conflict:
                        available_slots.append(str(current_time))
                    
                    # Move to next 30-minute slot
                    current_time = (
                        timezone.datetime.combine(timezone.datetime.today(), current_time) + 
                        timezone.timedelta(minutes=30)
                    ).time()
            
            return Response({'available_slots': available_slots})
        
        except ValueError:
            return Response(
                {'error': 'Định dạng ngày không hợp lệ. Sử dụng YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )


class DentistTimeOffViewSet(viewsets.ModelViewSet):
    """ViewSet for managing dentist time off."""
    
    queryset = DentistTimeOff.objects.all()
    serializer_class = DentistTimeOffSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAdminUser | IsDentistUser]
        else:
            permission_classes = [IsAdminUser | IsDentistUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Customize queryset based on user type."""
        user = self.request.user
        
        if user.user_type == user.UserType.DENTIST:
            return DentistTimeOff.objects.filter(dentist=user)
        elif user.user_type in [user.UserType.STAFF, user.UserType.ADMIN]:
            return DentistTimeOff.objects.all()
        
        return DentistTimeOff.objects.none()