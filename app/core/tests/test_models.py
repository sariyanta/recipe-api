"""
Tests for models.
"""

from multiprocessing.sharedctypes import Value

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

    def test_new_user_email_normalized(self):
        """Test if email is normalize for new users."""
        sample_emails = [
            ["test1@EXAMPLE.COM", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that when user create account without email raises error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "pass123")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser("test@example.com", "pass123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
