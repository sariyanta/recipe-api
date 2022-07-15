"""
Tests for recipe API.
"""


from decimal import Decimal

from core import models
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse("recipe:recipe-list")


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        "title": "Sample recipe title",
        "description": "Sample description",
        "time_minutes": 5,
        "price": 5.25,
        "link": "https://example.com/sample.pdf",
    }

    defaults.update(params)

    recipe = models.Recipe.objects.create(user=user, **defaults)

    return recipe


def detail_url(recipe_id):
    """Create and return detail url for recipe."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_user(**params):
    """Create user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeTests(TestCase):
    """Test public api."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeTests(TestCase):
    """Test authorized public api."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = models.Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test recipe is limited to only authenticated user."""
        other_user = create_user(
            email="other_user@example.com",
            password="testpass123",
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = models.Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test recipe detail."""

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_api_success(self):
        """Test creating recipe from the api"""
        payload = {
            "title": "Sample recipe title",
            "time_minutes": 5,
            "price": 5.25,
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = models.Recipe.objects.get(id=res.data["id"])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = "https://example.com/original.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Recipe title",
            link=original_link,
        )

        payload = {
            "title": "New Title",
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)

    def test_full_update(self):
        """Test full update of a recipe."""

        recipe = create_recipe(
            user=self.user,
            title="Recipe title",
            description="Recipe description",
            link="https://example.com/original.pdf",
        )

        payload = {
            "title": "New recipe title",
            "description": "New recipe description",
            "link": "https://example.com/new.pdf",
            "time_minutes": 3,
            "price": Decimal(6),
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changin recipe user result in an error"""
        new_user = create_user(email="new@example.com", password="pass123")
        recipe = create_recipe(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_deleting_recipe(self):
        """Test removing a recipe"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(models.Recipe.objects.filter(id=recipe.id).exists())

    def test_deleting_other_user_recipe(self):
        """Test removing other user recipe"""
        other_user = create_user(email="new@example.com", password="pass123")
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(models.Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_new_tags(self):
        """Creating recipe with new tags"""

        payload = {
            "title": "Thai prawn curry",
            "time_minutes": 5,
            "price": Decimal(10),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = models.Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_existing_tag(self):
        """Creating recipe with existing tags"""
        tag_indian = models.Tag.objects.create(user=self.user, name="Indian")

        payload = {
            "title": "Pongal",
            "time_minutes": 5,
            "price": Decimal(10),
            "tags": [{"name": "Indian"}, {"name": "Breakfast"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = models.Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload["tags"]:
            exists = recipe.tags.filter(name=tag["name"], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tags when updating recipe"""
        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "Lunch"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = models.Tag.objects.filter(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning existing tag when creating a recipe"""
        tag_breakfast = models.Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = models.Tag.objects.create(user=self.user, name="Lunch")
        payload = {"tags": [{"name": "Lunch"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags."""
        tag = models.Tag.objects.create(user=self.user, name="Desserts")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": [{"name": []}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
