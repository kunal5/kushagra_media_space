from django.core.validators import RegexValidator

phone_number_validator = RegexValidator(
    regex=r"^\+?1?\d{9,16}$",
    message="Phone number must be entered in the format: '+999999999'. Up to 16 digits allowed.",
)
