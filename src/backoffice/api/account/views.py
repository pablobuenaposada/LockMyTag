from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Account
from api.account.serializers import AccountOutputSerializer
from api.fetcher import FetcherAuthentication, IsFetcher


class AccountListView(generics.ListAPIView):
    authentication_classes = [FetcherAuthentication]
    permission_classes = [IsFetcher]
    queryset = Account.objects.all()
    serializer_class = AccountOutputSerializer


class SessionLoginView(APIView):
    """
    Login with username/password once and receive a session cookie.
    Subsequent requests use the cookie for authentication.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        """Hands out the CSRF cookie the map needs to log out, since Django's
        LogoutView checks it."""
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        user = authenticate(
            request,
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user is None:
            return Response(
                {"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
            )
        login(request, user)
        return Response({"detail": "ok"})
