#!/usr/bin/env python3
"""
Security Keys Generator for Causal Affect Platform

Generates all required secret keys for deployment.
Run this script and save the output securely!
"""

import secrets
from cryptography.fernet import Fernet

print("=" * 70)
print("🔐 CAUSAL AFFECT PLATFORM - SECURITY KEYS GENERATOR")
print("=" * 70)
print()
print("⚠️  IMPORTANT: Save these keys securely!")
print("   - Store in password manager (1Password, LastPass, etc.)")
print("   - NEVER commit to Git")
print("   - Use different keys for dev/staging/production")
print()
print("=" * 70)
print()

# Generate keys
secret_key = secrets.token_urlsafe(32)
jwt_secret_key = secrets.token_urlsafe(32)
encryption_key = Fernet.generate_key().decode()

print("📋 COPY THESE TO YOUR .env FILE:")
print("-" * 70)
print(f"SECRET_KEY={secret_key}")
print(f"JWT_SECRET_KEY={jwt_secret_key}")
print(f"ENCRYPTION_KEY={encryption_key}")
print()

print("=" * 70)
print()
print("📋 RAILWAY DEPLOYMENT COMMANDS:")
print("-" * 70)
print(f'railway variables set SECRET_KEY="{secret_key}"')
print(f'railway variables set JWT_SECRET_KEY="{jwt_secret_key}"')
print(f'railway variables set ENCRYPTION_KEY="{encryption_key}"')
print()

print("=" * 70)
print()
print("✅ NEXT STEPS:")
print("   1. Copy the .env values above to your local .env file")
print("   2. Run the Railway commands above to set production variables")
print("   3. Delete this script output after saving keys")
print()
print("=" * 70)
