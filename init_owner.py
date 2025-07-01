#!/usr/bin/env python3
"""
Initialize owner account for Multi-Tenant Time Tracking System
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# Database setup
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def create_owner_account():
    """Create initial owner account"""
    
    # Check if owner already exists
    existing_owner = await db.owners.find_one({"username": "owner"})
    if existing_owner:
        print("✅ Owner account already exists!")
        print(f"Username: {existing_owner['username']}")
        print(f"Email: {existing_owner['email']}")
        return
    
    # Create owner account
    owner_data = {
        "id": str(uuid.uuid4()),
        "username": "owner",
        "email": "owner@system.com",
        "password_hash": get_password_hash("owner123"),
        "created_at": datetime.utcnow()
    }
    
    await db.owners.insert_one(owner_data)
    
    print("🎉 Owner account created successfully!")
    print("=" * 50)
    print("📋 Login credentials:")
    print("Username: owner")
    print("Password: owner123")
    print("Email: owner@system.com")
    print("=" * 50)
    print("🔗 Login URL: https://f332c407-65e9-4037-992d-6ec897157efb.preview.emergentagent.com/")
    print("💡 Use these credentials to log in as system owner")

async def main():
    try:
        await create_owner_account()
    except Exception as e:
        print(f"❌ Error creating owner account: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())