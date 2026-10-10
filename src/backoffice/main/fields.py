"""JSON stored as an encrypted blob.

django-encrypted-model-fields handles the cipher; this only adds the JSON on
top of it, because the package has no JSON field of its own and its text field
would otherwise store a value's repr.
"""

import json

from encrypted_model_fields.fields import EncryptedTextField


class EncryptedJSONField(EncryptedTextField):
    """Encrypts the whole document, so no key or value is readable in a dump."""

    def get_db_prep_save(self, value, connection):
        # str() on a dict gives a Python repr, which will not parse back as JSON
        if value is not None and not isinstance(value, str):
            value = json.dumps(value)
        return super().get_db_prep_save(value, connection)

    def from_db_value(self, value, *args, **kwargs):
        value = super().from_db_value(value, *args, **kwargs)
        return None if value is None else json.loads(value)
