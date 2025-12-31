#!/usr/bin/env python3
"""
Generate a secure JWT secret key for production deployment
"""
import secrets

if __name__ == "__main__":
    secret = secrets.token_urlsafe(32)
    print("\n" + "="*60)
    print("🔐 SECURE JWT SECRET KEY GENERATED")
    print("="*60)
    print("\nCopy this value to Railway environment variables:")
    print("\nJWT_SECRET_KEY=" + secret)
    print("\n" + "="*60)
    print("\n⚠️  IMPORTANT: Keep this secret safe and never commit to Git!")
    print("="*60 + "\n")
