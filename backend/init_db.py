import asyncio

from dotenv import load_dotenv

load_dotenv()


async def init_db():
    print(
        "WARNING: init_db.py is deprecated. Use Alembic for migrations: alembic upgrade head"
    )


if __name__ == "__main__":
    asyncio.run(init_db())
