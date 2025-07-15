#!/usr/bin/env python3
"""Test authentication for nilukush@gmail.com"""

import asyncio
import sys
sys.path.append('/Users/nileshkumar/gh/prism/prism-core')

from passlib.context import CryptContext
from backend.src.services.auth import AuthService

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Test password verification
stored_hash = "$2b$12$o6OJ2bxyYKzwo63RiHxOm.hMPg.X1gi1IsmyY78uWlr1AzLDUwq5e"

# Common passwords to test
test_passwords = [
    "Test123!@#",
    "Test123!",
    "Test123",
    "test123",
    "password",
    "Password123!",
    "Nilukush123!",
    "nilukush123",
    "12345678"
]

print("Testing password verification for nilukush@gmail.com")
print("Stored hash:", stored_hash[:20] + "...")
print("\nTrying common passwords:")

for password in test_passwords:
    try:
        result = pwd_context.verify(password, stored_hash)
        print(f"  {password:<20} - {'MATCH!' if result else 'no match'}")
        if result:
            print(f"\n✅ Password found: {password}")
            break
    except Exception as e:
        print(f"  {password:<20} - error: {e}")