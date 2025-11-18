"""
Alembic Environment Configuration

Simplified configuration for manual migrations.
For autogenerate support, the Flask-SQLAlchemy metadata integration needs to be resolved.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Get database URI (hardcoded for now to avoid Flask-SQLAlchemy conflicts)
db_path = os.path.join(project_root, "instance", "kath.db")
db_path = os.path.abspath(db_path)

# Ensure directory exists
Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)

database_uri = f"sqlite:///{db_path}"

# Alembic Config object
config = context.config
config.set_main_option("sqlalchemy.url", database_uri)

# Interpret config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# For manual migrations, we don't need target_metadata
# For autogenerate, this would need to be set to Base.metadata
target_metadata = None


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
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = database_uri

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
