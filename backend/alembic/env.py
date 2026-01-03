"""
Alembic Environment Configuration for Legal AI System

This module configures Alembic to work with our database models and
environment-based configuration, without exposing credentials.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from root .env (two levels up from alembic/)
root_env = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=root_env)

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models' metadata here
# This is crucial for autogenerate support
try:
    from app.models.legal_documents import Base as LegalBase
    from app.models.user import Base as UserBase

    # Combine metadata from all model bases
    target_metadata = LegalBase.metadata

    # If you have multiple Base classes, you can combine them
    # For now, we'll use LegalBase which should include all models

except ImportError as e:
    print(f"WARNING: Could not import models: {e}")
    print("Autogenerate will not work properly without models imported")
    target_metadata = None

# Get database URL from environment variable
# Never hardcode database credentials!
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Default to SQLite for development if not set
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    if ENVIRONMENT == 'production':
        raise ValueError("DATABASE_URL must be set in production environment!")
    else:
        DATABASE_URL = 'sqlite:///./legal_ai.db'
        print(f"Using default SQLite database for development")

# Override the sqlalchemy.url from alembic.ini with our environment variable
config.set_main_option('sqlalchemy.url', DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect default value changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
