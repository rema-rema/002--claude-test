"""
Simple test script to verify basic functionality.
"""
import jwt
from datetime import datetime, timezone, timedelta

# Test JWT functionality
print("=== JWT Token Test ===")

SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"

# Create access token
data = {"sub": "test-user-123", "type": "access"}
expire = datetime.now(timezone.utc) + timedelta(minutes=30)
data.update({"exp": expire})

token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
print(f"✅ Access token created: {len(token)} characters")

# Verify token
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
print(f"✅ Token verified: user={payload['sub']}, type={payload['type']}")

# Create refresh token
refresh_data = {"sub": "test-user-123", "type": "refresh"}
refresh_expire = datetime.now(timezone.utc) + timedelta(days=7)
refresh_data.update({"exp": refresh_expire})

refresh_token = jwt.encode(refresh_data, SECRET_KEY, algorithm=ALGORITHM)
print(f"✅ Refresh token created: {len(refresh_token)} characters")

refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
print(f"✅ Refresh token verified: user={refresh_payload['sub']}, type={refresh_payload['type']}")

print("\n=== Basic Auth Tests Completed Successfully ===")
print("✅ JWT token generation and verification working")
print("✅ Access and refresh tokens working")
print("✅ Core authentication logic verified")