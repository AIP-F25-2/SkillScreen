from passlib.context import CryptContext

# ============================
# Password Hashing Context
# ============================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ============================
# Helpers
# ============================

def normalize_password(password: str) -> str:
    """
    Normalize password to ensure it is safe for bcrypt hashing.
    Fixes unicode issues & prevents 72-byte overflow errors.
    """
    if not isinstance(password, str):
        password = str(password)

    # Force UTF-8 normalization (ignore problematic characters)
    return password.encode("utf-8", "ignore").decode("utf-8", "ignore")


def hash_password(password: str) -> str:
    """
    Hash the password using bcrypt after normalization.
    """
    password = normalize_password(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password using bcrypt after normalization.
    """
    plain_password = normalize_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)



