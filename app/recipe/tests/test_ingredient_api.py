"""
Tests for ingredients API.
"""
from decimal import Decimal

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer, RecipeSerializer
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

    def test_filter_ingredients_assigned_only(self):
        """Test filter ingredients by those assigned to recipes"""

        ing_one = models.Ingredient.objects.create(user=self.user, name="Apples")
        ing_two = models.Ingredient.objects.create(user=self.user, name="Turkey")
        recipe = models.Recipe.objects.create(
            user=self.user, title="Apple Pie", time_minutes=5, price=Decimal("4.5")
        )
        recipe.ingredients.add(ing_one)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": "1"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = IngredientSerializer(ing_one)
        s2 = IngredientSerializer(ing_two)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self):
        """Test filter ingredients return unique only"""
        ing = models.Ingredient.objects.create(user=self.user, name="Eggs")
        models.Ingredient.objects.create(user=self.user, name="Lentil")

        recipe_one = models.Recipe.objects.create(
            user=self.user, title="Egg and Bacon", time_minutes=5, price=Decimal("4.5")
        )
        recipe_two = models.Recipe.objects.create(
            user=self.user, title="Egg Benedict", time_minutes=5, price=Decimal("4.5")
        )

        recipe_one.ingredients.add(ing)
        recipe_two.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": "1"})

        self.assertEqual(len(res.data), 1)
