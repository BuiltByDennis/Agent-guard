# 1. This must happen before importing auth to prevent the RuntimeError
from dotenv import load_dotenv
load_dotenv()

import asyncio
from models import User
from database import AsyncSessionLocal
from auth import get_password_hash
from init_db import init_db

async def create_admin():
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")

    await init_db()

    async with AsyncSessionLocal() as session:
        hashed_pw = get_password_hash(password)
        new_user = User(
            email=email,
            hashed_password=hashed_pw,
            role="admin"
        )
        session.add(new_user)
        await session.commit()
        print(f"Admin user {email} created successfully!")

if __name__ == "__main__":
    asyncio.run(create_admin())
