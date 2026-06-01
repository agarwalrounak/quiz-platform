from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):
    def test_register_creates_user_role(self):
        resp = self.client.post(
            reverse("register"),
            {"username": "alice", "email": "a@x.com", "password": "s3cretpass99"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="alice")
        self.assertEqual(user.role, "user")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password("s3cretpass99"))

    def test_register_rejects_weak_password(self):
        resp = self.client.post(
            reverse("register"),
            {"username": "bob", "password": "123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_cannot_set_admin_role(self):
        # role is read-only on input; passing it must not escalate privileges.
        self.client.post(
            reverse("register"),
            {"username": "mallory", "password": "s3cretpass99", "role": "admin"},
            format="json",
        )
        self.assertEqual(User.objects.get(username="mallory").role, "user")


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="carol", password="s3cretpass99"
        )

    def test_login_returns_tokens_and_role(self):
        resp = self.client.post(
            reverse("login"),
            {"username": "carol", "password": "s3cretpass99"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["role"], "user")

    def test_login_wrong_password(self):
        resp = self.client.post(
            reverse("login"),
            {"username": "carol", "password": "nope"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class MeEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dave", password="s3cretpass99"
        )

    def test_me_requires_auth(self):
        self.assertEqual(
            self.client.get(reverse("me")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_returns_current_user(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("me"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "dave")


class SuperuserRoleTests(APITestCase):
    def test_createsuperuser_gets_admin_role(self):
        admin = User.objects.create_superuser(
            username="root", email="r@x.com", password="s3cretpass99"
        )
        self.assertEqual(admin.role, "admin")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_admin_role)
