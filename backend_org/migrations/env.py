import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from models.models import Base  # ✅ Import your SQLAlchemy models
from config.db import engine  # ✅ Import your database engine

# Load Alembic configuration
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ Set the metadata for Alembic autogenerate to recognize your models
target_metadata = Base.metadata

# ✅ Override database URL from Alembic.ini using environment variables
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "postgresql://root:root@db:5432/ai_chat_platform"))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
