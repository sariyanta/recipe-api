"""
Serializers for Recipe API.
"""

from core import models
from rest_framework import serializers


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe object"""

    class Meta:
        model = models.Recipe
        fields = ["id", "title", "time_minutes", "price", "link"]
        read_only_fields = ["id"]


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag object"""

    class Meta:
        model = models.Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]
