from django.urls import path

from api.account.views import AccountListView

urlpatterns = [
    path("", AccountListView.as_view(), name="account-list"),
]
