from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, DentistProfile
from .serializers import (
    UserSerializer, UserPublicSerializer, CustomerSerializer, 
    DentistSerializer, DentistProfileSerializer
)
from .permissions import IsAdminUser, IsDentistUser, IsStaffUser, IsSameUserOrAdmin


class LoginView(generics.GenericAPIView):
    """View for user login and token generation."""
    
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        
        if not phone_number or not password:
            return Response(
                {'error': 'Vui lòng cung cấp số điện thoại và mật khẩu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(phone_number=phone_number, password=password)
        
        if not user:
            return Response(
                {'error': 'Thông tin đăng nhập không chính xác'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Tài khoản của bạn đã bị khóa'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate token
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'full_name': user.full_name,
                'user_type': user.user_type
            }
        }
        
        return Response(data, status=status.HTTP_200_OK)


class CustomerRegistrationView(generics.CreateAPIView):
    """View for customer registration."""
    queryset = User.objects.filter(user_type=User.UserType.CUSTOMER)
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate token
            refresh = RefreshToken.for_user(user)
            
            # Prepare response data
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'phone_number': user.phone_number,
                    'full_name': user.full_name,
                    'user_type': user.user_type
                }
            }
            
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'create']:
            permission_classes = [IsAdminUser]
        elif self.action in ['update', 'partial_update', 'retrieve']:
            permission_classes = [IsSameUserOrAdmin]
        elif self.action == 'destroy':
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'public_list':
            return UserPublicSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Return the authenticated user's information."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def public_list(self, request):
        """Return a public list of users (id, name, type)."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], permission_classes=[IsAdminUser])
    def toggle_active(self, request):
        """Toggle user active status (for admin to disable/enable user accounts)."""
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(pk=user_id)
            user.is_active = not user.is_active
            user.save()
            return Response({'status': f'Tài khoản {"đã được kích hoạt" if user.is_active else "đã bị khóa"}.'})
        except User.DoesNotExist:
            return Response({'error': 'Không tìm thấy người dùng.'}, status=status.HTTP_404_NOT_FOUND)


class DentistViewSet(viewsets.ModelViewSet):
    """ViewSet for managing dentist users."""
    queryset = User.objects.filter(user_type=User.UserType.DENTIST)
    serializer_class = DentistSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def available(self, request):
        """Return a list of available dentists."""
        # Get active dentists
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)