"""
Tests for models.
"""

from decimal import Decimal
from multiprocessing.sharedctypes import Value

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase


def create_user(email="test@example.com", password="testpass123"):
    """Create and return user"""
    return get_user_model().objects.create_user(email, password)


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
        """Test creating a superuser"""

        user = get_user_model().objects.create_superuser("test@example.com", "pass123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe for authenticatd user"""

        user = get_user_model().objects.create_user("test@example.com", "testpass123")

        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe name",
            time_minutes=5,
            price=Decimal(5.50),
            description="Sample recipe description",
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tags(self):
        """Test creating tags is successfull"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag 1")

        self.assertEqual(str(tag), tag.name)
