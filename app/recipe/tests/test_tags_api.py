"""
Tests for the tags API.
"""
from decimal import Decimal

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import TagSerializer
from rest_framework import status
from rest_framework.test import APIClient

TAGS_URL = reverse("recipe:tag-list")


def create_user(email="test@example.com", password="testpass123"):
    """Create and return example user."""

    return get_user_model().objects.create_user(email, password)


def detail_url(tag_id):
    """Create and return tag usl"""
    return reverse("recipe:tag-detail", args=[tag_id])


class PublicTagAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_authorization_required(self):
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITests(TestCase):
    """Test authenticated requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags_list(self):
        """Test retrieving list of tags."""
        models.Tag.objects.create(user=self.user, name="Vegan")
        models.Tag.objects.create(user=self.user, name="Desserts")

        res = self.client.get(TAGS_URL)

        tags = models.Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_tags_limited_to_user(self):
        """Test retrieving list of tags created by user only."""
        other_user = create_user(email="test2@example.com", password="testpass123")

        models.Tag.objects.create(user=other_user, name="Fruity")
        tag = models.Tag.objects.create(user=self.user, name="Comfort food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], tag.id)
        self.assertEqual(res.data[0]["name"], tag.name)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = models.Tag.objects.create(user=self.user, name="After dinner")

        payload = {"name": "Dessert"}

        url = detail_url(tag.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()

        self.assertEqual(tag.name, payload["name"])

    def test_delte_tag(self):
        """Test deleting a tag"""
        tag = models.Tag.objects.create(user=self.user, name="Breakfast")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(models.Tag.objects.filter(user=self.user).exists())

    def test_filter_tags_assigned_only(self):
        """Test filter tags by those assigned to recipes"""
        tag_one = models.Tag.objects.create(user=self.user, name="Breakfast")
        tag_two = models.Tag.objects.create(user=self.user, name="Lunch")

        recipe = models.Recipe.objects.create(
            user=self.user, title="Apple Pie", time_minutes=5, price=Decimal("4.5")
        )

        recipe.tags.add(tag_one)

        res = self.client.get(TAGS_URL, {"assigned_only": "1"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = TagSerializer(tag_one)
        s2 = TagSerializer(tag_two)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        """Test filter tags returning unique only"""
        tag_one = models.Tag.objects.create(user=self.user, name="Brunch")
        models.Tag.objects.create(user=self.user, name="Dinner")

        recipe_one = models.Recipe.objects.create(
            user=self.user, title="Nasi Goreng", time_minutes=10, price=Decimal(5.5)
        )
        recipe_two = models.Recipe.objects.create(
            user=self.user, title="Sate Kambing", time_minutes=120, price=Decimal(15)
        )
        recipe_one.tags.add(tag_one)
        recipe_two.tags.add(tag_one)

        res = self.client.get(TAGS_URL, {"assigned_only": "1"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
