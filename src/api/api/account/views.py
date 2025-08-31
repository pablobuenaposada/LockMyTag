from rest_framework import generics

from account.models import Account
from api.account.serializers import AccountOutputSerializer


class AccountListView(generics.ListAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountOutputSerializer
