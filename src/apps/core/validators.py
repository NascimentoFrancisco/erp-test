from django.core.exceptions import ValidationError
from pycpfcnpj import cpfcnpj


def validate_document(value):
    if not value:
        raise ValidationError(
            "Dado obrigatório."
        )

    if not cpfcnpj.validate(value):
        raise ValidationError(
            f"O documento '{value}' é inválido. Insira um CPF ou CNPJ válido."
        )
