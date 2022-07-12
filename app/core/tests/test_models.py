"""
Tests for models.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTest(TestCase):
    """
    Test models.
    """

    def test_create_user_email_successfull(self):
        """Creating user with email is successfull"""

        email = "test@example.com"
        password = "123456890"
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
