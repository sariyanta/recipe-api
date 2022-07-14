"""
Serializers for Recipe API.
"""

from core import models
from rest_framework import serializers


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe object"""

    class Meta:
        model = models.Recipe
        fields = ["id", "title", "description", "time_minutes", "price", "link"]
        read_only_fields = ["id"]
