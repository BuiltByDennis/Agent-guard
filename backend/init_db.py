import asyncio
import os

from dotenv import load_dotenv

load_dotenv()


def _run_migrations() -> None:
    """Run `alembic upgrade head` synchronously.

    Alembic's env.py drives an async engine with its own asyncio.run(),
    so this must execute in a thread that has no running event loop.
    """
    from alembic import command
    from alembic.config import Config

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    command.upgrade(cfg, "head")


async def init_db() -> None:
    """Apply all pending migrations. Idempotent; called on app startup so
    every deployment path (Docker entrypoint, Render, local) converges —
    not just the ones whose start command remembers to run Alembic."""
    await asyncio.to_thread(_run_migrations)


if __name__ == "__main__":
    asyncio.run(init_db())
