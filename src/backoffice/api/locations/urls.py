from django.urls import path

from api.locations.views import LatestTagLocationView, TagLocationCreateView

urlpatterns = [
    path("", TagLocationCreateView.as_view(), name="locations-create"),
    path(
        "latest/<uuid:tag_id>",
        LatestTagLocationView.as_view(),
        name="latest-tag-location",
    ),
]
