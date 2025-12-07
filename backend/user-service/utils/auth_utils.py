import bcrypt
import hashlib
import base64

# ============================
# Helpers
# ============================

def normalize_password(password: str) -> str:
    """
    Normalize password to ensure it is safe for hashing.
    """
    if not isinstance(password, str):
        password = str(password)

    # Force UTF-8 normalization (ignore problematic characters)
    return password.encode("utf-8", "ignore").decode("utf-8", "ignore")


def hash_password(password: str) -> str:
    """
    Hash the password using bcrypt after normalization and SHA-256 pre-hashing.
    """
    password = normalize_password(password)
    
    # Pre-hash with SHA-256 to bypass bcrypt's 72-byte limit
    sha256_hash = hashlib.sha256(password.encode('utf-8')).digest()
    # Encode in base64 to get a string representation safe for bcrypt
    password_b64 = base64.b64encode(sha256_hash)
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_b64, salt)
    
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password using bcrypt after normalization and SHA-256 pre-hashing.
    """
    plain_password = normalize_password(plain_password)
    
    # Pre-hash with SHA-256 to match the hashing strategy
    sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).digest()
    plain_password_b64 = base64.b64encode(sha256_hash)
    
    # Verify hash
    try:
        return bcrypt.checkpw(plain_password_b64, hashed_password.encode('utf-8'))
    except ValueError:
        return False



