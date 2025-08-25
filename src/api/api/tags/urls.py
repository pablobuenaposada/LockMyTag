from django.urls import path

from api.tags.views import TagListView

urlpatterns = [
    path("", TagListView.as_view(), name="tags-list"),
]
