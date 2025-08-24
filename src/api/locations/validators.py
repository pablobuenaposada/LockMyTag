from django.core.exceptions import ValidationError


def validate_empty(value):
    if not value:
        raise ValidationError("This field cannot be emtpy")
