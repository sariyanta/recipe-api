"""
Views for Recipe API.
"""

from core import models
from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from recipe import serializers


class RecipeViewSets(viewsets.ModelViewSet):
    """Viewsets for Recipe list"""

    serializer_class = serializers.RecipeDetailSerializer
    queryset = models.Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipe of only the authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """Retrieve serializer class"""
        if self.action == "list":
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)


class TagViewSets(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Viewsets for recipe"""

    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve tags of only the authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by("-name")
