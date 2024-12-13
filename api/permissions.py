from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return IsAuthenticated().has_permission(request, view) and request.user.is_admin


class IsStudentUser(BasePermission):
    def has_permission(self, request, view):
        return IsAuthenticated().has_permission(request, view) and request.user.is_student


class IsCollegeUser(BasePermission):
    def has_permission(self, request, view):
        return IsAuthenticated().has_permission(request, view) and request.user.is_college