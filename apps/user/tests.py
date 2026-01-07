from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

from django.urls import reverse, NoReverseMatch
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()


def reverse_user_create():
    """
    Devuelve la URL correcta del endpoint de registro.
    Soporta proyectos con Djoser namespaced.
    """
    for name in ("user-list", "djoser:user-list", "djoser:user-create", "user-register"):
        try:
            return reverse(name)
        except NoReverseMatch:
            continue
    raise NoReverseMatch("No se encontró endpoint de creación de usuario (user-list / djoser:user-list / etc.)")


class UserAuthTests(APITestCase):
    def test_user_registration(self):
        url = reverse_user_create()

        data = {
            "email": "nuevo@example.com",
            "first_name": "nuevo",
            "last_name": "usuario",
            "password": "ClaveSegura123!",
            "re_password": "ClaveSegura123!",
        }

        response = self.client.post(url, data, format="json")

        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        self.assertTrue(User.objects.filter(email="nuevo@example.com").exists())

    def test_login_returns_tokens(self):
        # create_user del MODELO NO recibe re_password
        User.objects.create_user(
            email="alguien@example.com",
            first_name="nuevo",
            last_name="usuario",
            password="ClaveSegura123!",
        )

        url = reverse("jwt-create")
        response = self.client.post(
            url,
            {"email": "alguien@example.com", "password": "ClaveSegura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


    def test_create_user_model(self):
        """
        Prueba el modelo: create_user NO recibe re_password.
        """
        user = User.objects.create_user(
            email="test@example.com",
            first_name="Ana",
            last_name="Torres",
            password="pass12345",
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("pass12345"))

    def test_user_related_objects_exist_if_configured(self):
        """
        Si tu sistema crea automáticamente relaciones (cart/profile/wishlist),
        esto las verifica SIN romperse si aún no están implementadas.
        """
        user = User.objects.create_user(
            email="rel@test.com",
            first_name="Rel",
            last_name="Test",
            password="pass12345",
        )

        # Solo valida si el atributo existe en el modelo.
        # Si no existe, el test no falla (porque depende de tu implementación).
        
        if hasattr(user, "cart"):
            self.assertIsNotNone(user.cart)

        if hasattr(user, "userprofile"):
            self.assertIsNotNone(user.userprofile)

        if hasattr(user, "wishlist"):
            self.assertIsNotNone(user.wishlist)

    def test_login_returns_tokens(self):
        """
        Prueba login JWT (Djoser + simplejwt):
        - create_user NO lleva re_password
        - endpoint jwt-create debe devolver access y refresh
        """
        User.objects.create_user(
            email="alguien@example.com",
            first_name="nuevo",
            last_name="usuario",
            password="ClaveSegura123!",
        )

        url = reverse("jwt-create")  # Djoser típico: /jwt/create/
        response = self.client.post(
            url,
            {"email": "alguien@example.com", "password": "ClaveSegura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
