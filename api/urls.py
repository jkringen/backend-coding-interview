from django.urls import path

from .views import (
    HealthCheckView,
    PhotographerPhotosView,
    PhotographersView,
    PhotographerView,
    PhotosView,
    PhotoView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # AUTHENTICATION VIEWS
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # PHOTO VIEWS
    path("photographers", PhotographersView.as_view(), name="api_photographers"),
    path(
        "photographers/<int:photographer_id>",
        PhotographerView.as_view(),
        name="api_photographers",
    ),
    path(
        "photographers/<int:photographer_id>/photos",
        PhotographerPhotosView.as_view(),
        name="api_photographers_photos",
    ),
    path("photos", PhotosView.as_view(), name="api_photos"),
    path("photos/<int:photo_id>", PhotoView.as_view(), name="api_photo"),
    # HEALTHCHECK
    path("health", HealthCheckView.as_view(), name="api_healthcheck"),
]
