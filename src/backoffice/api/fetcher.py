"""How the fetcher talks to the API: a shared secret, not a Django user.

The fetcher has no business in the admin or on the map, so it is not given an
account that could log into either. It sends FETCHER_TOKEN as a bearer token
and only the endpoints that serve it accept that.
"""

import hmac

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework.settings import api_settings


class Fetcher:
    """Stands in for request.user when the fetcher is calling."""

    is_authenticated = True
    is_anonymous = False
    is_active = True
    is_staff = False
    is_superuser = False
    pk = None
    username = "fetcher"

    def __str__(self):
        return self.username


class FetcherAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != self.keyword:
            return None  # not ours; let the other authenticators look at it

        expected = settings.FETCHER_TOKEN.encode()
        # Without a configured token nothing may pass, an empty one included
        if (
            len(parts) != 2
            or not expected
            or not hmac.compare_digest(parts[1], expected)
        ):
            raise AuthenticationFailed("Invalid token.")
        return Fetcher(), None

    def authenticate_header(self, request):
        return "Bearer"


def is_fetcher(request):
    return isinstance(request.user, Fetcher)


class IsFetcher(BasePermission):
    def has_permission(self, request, view):
        return is_fetcher(request)


# For the endpoints the map uses too: the fetcher's token next to the usual logins
FETCHER_OR_USER_AUTHENTICATION = [
    FetcherAuthentication,
    *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
]
