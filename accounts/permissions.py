from rest_framework import permissions
from .models import User


class IsAdminUser(permissions.BasePermission):
    """
    Permission to allow only admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == User.UserType.ADMIN


class IsDentistUser(permissions.BasePermission):
    """
    Permission to allow only dentist users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == User.UserType.DENTIST


class IsStaffUser(permissions.BasePermission):
    """
    Permission to allow only staff users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == User.UserType.STAFF


class IsCustomerUser(permissions.BasePermission):
    """
    Permission to allow only customer users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == User.UserType.CUSTOMER


class IsSameUserOrAdmin(permissions.BasePermission):
    """
    Permission to allow users to access only their own resources,
    or admin users to access any resource.
    """
    def has_object_permission(self, request, view, obj):
        # Admin users can access any resource
        if request.user.user_type == User.UserType.ADMIN:
            return True
        
        # Users can access only their own resources
        return obj.id == request.user.id