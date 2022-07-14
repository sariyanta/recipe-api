"""
URL mappings for the recipe
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register("recipes", views.RecipeViewSets)

app_name = "recipe"

urlpatterns = [path("", include(router.urls))]
