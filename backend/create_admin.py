import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from database import AsyncSessionLocal
from auth import get_password_hash

async def create_admin():
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    
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
