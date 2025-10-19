from django.urls import path

from api.locks.views import LockListByTagView

urlpatterns = [
    path("<uuid:tag_id>", LockListByTagView.as_view(), name="locks-by-tag"),
]
