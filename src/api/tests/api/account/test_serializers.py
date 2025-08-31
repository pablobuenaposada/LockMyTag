import pytest
from model_bakery import baker

from account.models import Account
from api.account.serializers import AccountOutputSerializer


@pytest.mark.django_db
class TestsAccountOutputSerializer:
    serializer_class = AccountOutputSerializer

    def test_success(self):
        account = baker.make(Account)

        assert self.serializer_class(account).data == {
            "id": account.id,
            "data": account.data,
            "created": account.created.isoformat().replace("+00:00", "Z"),
            "modified": account.modified.isoformat().replace("+00:00", "Z"),
        }
