from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """Allows access only to users with the admin role."""

    message = "Admin role required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_admin_role", False)
        )


class IsAdminOrReadOnly(BasePermission):
    """Authenticated users may read; only admins may write."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "is_admin_role", False)


class IsOwner(BasePermission):
    """Object-level permission: only the owner (or an admin) may access."""

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_admin_role", False):
            return True
        owner = getattr(obj, "user", None)
        return owner == request.user
