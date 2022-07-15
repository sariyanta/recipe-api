"""
Tests for ingredients API.
"""

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from rest_framework import status
from rest_framework.test import APIClient

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_user(email="user@example.com", password="testpass123"):
    """Create and return user"""
    return get_user_model().objects.create_user(email, password)


def detail_url(ingredient_id):
    """Create and return ingredient url"""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


class PublicIngredientAPITest(TestCase):
    """Test unauthenticated API request"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):
    """Tests authorized API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving list of ingredients."""
        models.Ingredient.objects.create(user=self.user, name="Kale")
        models.Ingredient.objects.create(user=self.user, name="Vanilla")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredients = models.Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(ingredients.count(), 2)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Test retrieving list only of the authenticated user"""
        other_user = create_user(email="other@example.com", password="testpass123")

        models.Ingredient.objects.create(user=other_user, name="Salt")
        ingredient = models.Ingredient.objects.create(user=self.user, name="Pepper")

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_ingredient_update(self):
        """Test updating ingredient"""
        ingredient = models.Ingredient.objects.create(user=self.user, name="Cilantro")
        payload = {"name": "Coriander"}

        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_ingredient_delete(self):
        """Test deleting ingredient"""

        ingredient = models.Ingredient.objects.create(user=self.user, name="Cilantro")

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = models.Ingredient.objects.filter(user=self.user)

        self.assertFalse(ingredients.exists())
