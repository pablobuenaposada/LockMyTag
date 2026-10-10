from rest_framework import serializers

from account.models import Account


class AccountOutputSerializer(serializers.ModelSerializer):
    # The field is text in the database, so DRF would otherwise render the
    # decrypted value as a string and the fetcher would get a repr, not an object
    data = serializers.JSONField()

    class Meta:
        model = Account
        fields = "__all__"
