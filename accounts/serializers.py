from rest_framework import serializers
from .models import User, DentistProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'password', 'full_name', 'date_of_birth', 
                  'address', 'user_type', 'is_active')
        read_only_fields = ('id', 'is_active')
    
    def create(self, validated_data):
        """Create and return a new user instance."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer for public User data."""
    
    class Meta:
        model = User
        fields = ('id', 'full_name', 'user_type')
        read_only_fields = fields


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer users."""
    
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'password', 'full_name', 'date_of_birth', 'address')
        read_only_fields = ('id',)
    
    def create(self, validated_data):
        """Create and return a new customer user instance."""
        password = validated_data.pop('password')
        user = User(**validated_data, user_type=User.UserType.CUSTOMER)
        user.set_password(password)
        user.save()
        return user


class DentistProfileSerializer(serializers.ModelSerializer):
    """Serializer for DentistProfile model."""
    
    class Meta:
        model = DentistProfile
        fields = ('id', 'specialization')


class DentistSerializer(serializers.ModelSerializer):
    """Serializer for Dentist users with profile."""
    
    dentist_profile = DentistProfileSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'password', 'full_name', 'date_of_birth', 
                  'address', 'is_active', 'dentist_profile')
        read_only_fields = ('id', 'is_active')
    
    def create(self, validated_data):
        """Create and return a new dentist user instance with profile."""
        profile_data = validated_data.pop('dentist_profile', None)
        password = validated_data.pop('password')
        
        user = User(**validated_data, user_type=User.UserType.DENTIST)
        user.set_password(password)
        user.save()
        
        if profile_data:
            DentistProfile.objects.create(user=user, **profile_data)
        else:
            DentistProfile.objects.create(user=user)
            
        return user
    
    def update(self, instance, validated_data):
        """Update a dentist user instance with profile."""
        profile_data = validated_data.pop('dentist_profile', None)
        password = validated_data.pop('password', None)
        
        # Update password if provided
        if password:
            instance.set_password(password)
            
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile if data provided
        if profile_data and hasattr(instance, 'dentist_profile'):
            for attr, value in profile_data.items():
                setattr(instance.dentist_profile, attr, value)
            instance.dentist_profile.save()
            
        return instance