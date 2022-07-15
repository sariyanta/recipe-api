"""
Tests for the tags API.
"""

from core.models import Tag
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
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Desserts")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_tags_limited_to_user(self):
        """Test retrieving list of tags created by user only."""
        other_user = create_user(email="test2@example.com", password="testpass123")

        Tag.objects.create(user=other_user, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Comfort food")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], tag.id)
        self.assertEqual(res.data[0]["name"], tag.name)

    def test_update_tag(self):
        """Test updating a tag"""
        tag = Tag.objects.create(user=self.user, name="After dinner")

        payload = {"name": "Dessert"}

        url = detail_url(tag.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()

        self.assertEqual(tag.name, payload["name"])

    def test_delte_tag(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name="Breakfast")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())
