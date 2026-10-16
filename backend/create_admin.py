import asyncio
import getpass

from dotenv import load_dotenv

from auth import get_password_hash
from database import AsyncSessionLocal
from init_db import init_db
from models import User

# Load .env before anything reads settings. database.py also calls
# load_dotenv() at import time, and core.config reads .env itself, so
# importing first is safe; this call is kept for explicitness.
load_dotenv()


async def create_admin():
    email = input("Enter admin email: ")
    password = getpass.getpass("Enter admin password: ")

    await init_db()

    async with AsyncSessionLocal() as session:
        hashed_pw = get_password_hash(password)
        new_user = User(email=email, hashed_password=hashed_pw, role="admin")
        session.add(new_user)
        await session.commit()
        print(f"Admin user {email} created successfully!")


if __name__ == "__main__":
    asyncio.run(create_admin())
