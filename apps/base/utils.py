import secrets
import string


def generate_otp(length: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def normalize_email(email: str) -> str:
    return email.strip().lower()


def generate_reference_code(prefix: str = "REF", length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}-{code}"