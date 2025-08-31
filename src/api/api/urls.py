from django.urls import include, re_path

app_name = "api"

urlpatterns = [
    re_path("tags/", include("api.tags.urls")),
    re_path("locations/", include("api.locations.urls")),
    re_path("account/", include("api.account.urls")),
]
