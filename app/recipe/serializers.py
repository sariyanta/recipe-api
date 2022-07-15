"""
Serializers for Recipe API.
"""

from core import models
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag object"""

    class Meta:
        model = models.Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe object"""

    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = models.Recipe
        fields = ["id", "title", "time_minutes", "price", "link", "tags"]
        read_only_fields = ["id"]

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tags"""
        auth_user = self.context["request"].user

        for tag in tags:
            tag_object, created = models.Tag.objects.get_or_create(
                user=auth_user, **tag
            )
            recipe.tags.add(tag_object)

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop("tags", [])
        recipe = models.Recipe.objects.create(**validated_data)

        self._get_or_create_tags(tags, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update recipe"""
        tags = validated_data.pop("tags", None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
