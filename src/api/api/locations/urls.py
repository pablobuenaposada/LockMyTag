from django.urls import path

from api.locations.views import TagLocationCreateView

urlpatterns = [
    path("", TagLocationCreateView.as_view(), name="locations-create"),
]
