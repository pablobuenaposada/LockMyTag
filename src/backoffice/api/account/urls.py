from django.contrib.auth.views import LogoutView
from django.urls import path

from api.account.views import AccountListView, SessionLoginView

urlpatterns = [
    path("", AccountListView.as_view(), name="account-list"),
    path("login/", SessionLoginView.as_view(), name="session-login"),
    path("logout/", LogoutView.as_view(next_page="/"), name="session-logout"),
]
