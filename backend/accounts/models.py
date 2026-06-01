from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    USER = "user", "User"


class CustomUserManager(UserManager):
    """Ensures superusers are also tagged with the admin role."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Application user with a coarse role used for API authorization.

    `role` drives DRF permissions (admin manages the question bank / review queue;
    user takes quizzes). Admins are also `is_staff` so they can reach Django admin.
    """

    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.USER
    )

    objects = CustomUserManager()

    @property
    def is_admin_role(self):
        return self.role == Role.ADMIN

    def save(self, *args, **kwargs):
        # Keep Django-admin access (is_staff) in sync with the admin role.
        if self.role == Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)
